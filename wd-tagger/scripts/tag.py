#!/usr/bin/env python3
"""
wd-tagger: 通过 HuggingFace Gradio API 调用 SmilingWolf wd-tagger 打标。

用法:
  python3 tag.py <图片路径> [--model <模型>] [--gen-threshold <浮点>]
                 [--char-threshold <浮点>] [--use-mcut] [--format text|json]
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error

API_BASE = "https://smilingwolf-wd-tagger.hf.space"

DEFAULT_MODEL = "SmilingWolf/wd-vit-tagger-v3"

MODELS = [
    "SmilingWolf/wd-swinv2-tagger-v3",
    "SmilingWolf/wd-convnext-tagger-v3",
    "SmilingWolf/wd-vit-tagger-v3",
    "SmilingWolf/wd-vit-large-tagger-v3",
    "SmilingWolf/wd-eva02-large-tagger-v3",
    "SmilingWolf/wd-v1-4-moat-tagger-v2",
    "SmilingWolf/wd-v1-4-swinv2-tagger-v2",
    "SmilingWolf/wd-v1-4-convnext-tagger-v2",
    "SmilingWolf/wd-v1-4-convnextv2-tagger-v2",
    "SmilingWolf/wd-v1-4-vit-tagger-v2",
    "deepghs/idolsankaku-swinv2-tagger-v1",
    "deepghs/idolsankaku-eva02-large-tagger-v1",
]


def upload_image(image_path: str) -> str:
    """上传图片到 Gradio Space，返回服务器端路径。"""
    boundary = "----MinisFormBoundary7MA4YWxkTrZu0gW"

    with open(image_path, "rb") as f:
        img_data = f.read()

    filename = os.path.basename(image_path)
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="files"; filename="{filename}"\r\n'.encode()
    body += b"Content-Type: application/octet-stream\r\n\r\n"
    body += img_data
    body += f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{API_BASE}/gradio_api/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())
        return result[0]


def predict(image_path: str, model: str, gen_threshold: float,
            use_mcut: bool, char_threshold: float, use_mcut_char: bool) -> dict:
    """上传图片并调用 Gradio predict API。"""
    server_path = upload_image(image_path)

    payload = {
        "data": [
            {"path": server_path},
            model,
            gen_threshold,
            use_mcut,
            char_threshold,
            use_mcut_char,
        ]
    }

    req = urllib.request.Request(
        f"{API_BASE}/gradio_api/call/predict",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        event_id = json.loads(resp.read().decode())["event_id"]

    # Poll for result (SSE)
    for _ in range(30):
        time.sleep(1.5)
        try:
            req2 = urllib.request.Request(
                f"{API_BASE}/gradio_api/call/predict/{event_id}"
            )
            with urllib.request.urlopen(req2) as resp2:
                raw = resp2.read().decode()
        except urllib.error.HTTPError:
            continue

        lines = raw.strip().split("\n")
        for i, line in enumerate(lines):
            if line.startswith("event: complete") or line.startswith("event: process_completed"):
                # Next line should be data:
                if i + 1 < len(lines) and lines[i + 1].startswith("data: "):
                    return json.loads(lines[i + 1][6:])

    raise TimeoutError("API 超时，请稍后重试")


def format_text(result: list) -> str:
    """格式化输出为人类可读文本。"""
    tags_str = result[0] if result[0] else ""
    rating_data = result[1] if len(result) > 1 else {}
    chars_data = result[2] if len(result) > 2 else {}

    lines = []
    if rating_data:
        label = rating_data.get("label", "?")
        confs = rating_data.get("confidences", [])
        top_conf = confs[0]["confidence"] * 100 if confs else 0
        lines.append(f"=== 评级 ===\n{label} ({top_conf:.1f}%)")

    if chars_data and chars_data.get("label"):
        lines.append(f"\n=== 角色 ===\n{chars_data['label']}")

    if tags_str:
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        lines.append(f"\n=== 标签 ({len(tags)}个) ===\n" + ", ".join(tags))

    return "\n".join(lines)


def format_json(result: list) -> str:
    """格式化输出为 JSON。"""
    tags_str = result[0] if result[0] else ""
    tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
    rating_data = result[1] if len(result) > 1 else {}
    chars_data = result[2] if len(result) > 2 else {}

    output = {
        "tags": tags,
        "tags_raw": tags_str,
        "rating": rating_data,
        "characters": chars_data,
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="wd-tagger: 给图片打 Danbooru 风格标签")
    parser.add_argument("image", help="图片路径（支持本地文件）")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        choices=MODELS, help="打标模型")
    parser.add_argument("--gen-threshold", type=float, default=0.35,
                        help="通用标签阈值 (0-1)")
    parser.add_argument("--char-threshold", type=float, default=0.35,
                        help="角色标签阈值 (0-1)")
    parser.add_argument("--use-mcut", action="store_true",
                        help="启用 MCut 自适应阈值")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="输出格式")

    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"错误: 图片不存在: {args.image}", file=sys.stderr)
        sys.exit(1)

    result = predict(
        args.image,
        args.model,
        args.gen_threshold,
        args.use_mcut,
        args.char_threshold,
        args.use_mcut,
    )

    if args.format == "json":
        print(format_json(result))
    else:
        print(format_text(result))


if __name__ == "__main__":
    main()
