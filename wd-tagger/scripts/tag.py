#!/usr/bin/env python3
"""
wd-tagger: 给图片打 Danbooru 风格标签。

后端:
  space   - HuggingFace Gradio Space（免费，CPU，约 10s）
  colab   - 自建 Colab GPU API（需自启，<1s，需填 API 地址）

用法:
  python3 tag.py <图片>                          # 使用 Space（默认）
  python3 tag.py <图片> --api colab --api-url <URL>  # 使用 Colab
  python3 tag.py <图片> --api colab                 # 使用 $WD_TAGGER_URL
"""

import argparse, base64, json, os, ssl, sys, time, urllib.request, urllib.error
import warnings

# Suppress SSL warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Try to use requests for better SSL/proxy compat
try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False
    # Fallback: install a permissive SSL context for urllib
    _ssl_ctx = ssl.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = ssl.CERT_NONE
    _https_handler = urllib.request.HTTPSHandler(context=_ssl_ctx)
    urllib.request.install_opener(urllib.request.build_opener(_https_handler))

# ── Space API ──
SPACE_BASE = "https://smilingwolf-wd-tagger.hf.space"
SPACE_MODELS = [
    "SmilingWolf/wd-swinv2-tagger-v3",
    "SmilingWolf/wd-vit-tagger-v3",
    "SmilingWolf/wd-eva02-large-tagger-v3",
    "SmilingWolf/wd-v1-4-moat-tagger-v2",
]
DEFAULT_MODEL = "SmilingWolf/wd-vit-tagger-v3"


def tag_space(image_path, model, gen_thresh, use_mcut, char_thresh):
    """通过 Gradio Space API 打标。"""
    filename = os.path.basename(image_path)

    if _HAS_REQUESTS:
        # 上传图片
        with open(image_path, "rb") as f:
            r = _requests.post(f"{SPACE_BASE}/gradio_api/upload",
                               files={"files": (filename, f, "application/octet-stream")},
                               verify=False, timeout=30)
        server_path = r.json()[0]

        # 推理
        payload = {"data": [{"path": server_path, "meta": {"_type": "gradio.FileData"}},
                            model, gen_thresh, use_mcut, char_thresh, use_mcut]}
        r2 = _requests.post(f"{SPACE_BASE}/gradio_api/call/predict",
                            json=payload, verify=False, timeout=30)
        event_id = r2.json()["event_id"]

        r3 = _requests.get(f"{SPACE_BASE}/gradio_api/call/predict/{event_id}",
                           verify=False, timeout=120, stream=True)
        for line in r3.iter_lines():
            if line:
                decoded = line.decode()
                if decoded.startswith("event:") and "error" in decoded:
                    raise RuntimeError("Space API returned error")
                if decoded.startswith("data:"):
                    data = json.loads(decoded[5:].strip())
                    if isinstance(data, list) and len(data) >= 4:
                        return _parse_space(data)
        raise TimeoutError("Space API 超时")
    else:
        # urllib fallback
        boundary = "----MinisFormBoundary"
        with open(image_path, "rb") as f:
            img_data = f.read()
        body = b""
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"{filename}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
        body += img_data
        body += f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(f"{SPACE_BASE}/gradio_api/upload", data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(req) as r:
            server_path = json.loads(r.read())[0]

        payload = {"data": [{"path": server_path, "meta": {"_type": "gradio.FileData"}},
                            model, gen_thresh, use_mcut, char_thresh, use_mcut]}
        req = urllib.request.Request(f"{SPACE_BASE}/gradio_api/call/predict",
            data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            event_id = json.loads(r.read())["event_id"]

        for _ in range(40):
            time.sleep(1)
            try:
                req2 = urllib.request.Request(f"{SPACE_BASE}/gradio_api/call/predict/{event_id}")
                with urllib.request.urlopen(req2) as r2:
                    raw = r2.read().decode()
            except urllib.error.HTTPError:
                continue
            lines = raw.strip().split("\n")
            for i, line in enumerate(lines):
                if "event: complete" in line:
                    if i + 1 < len(lines) and lines[i + 1].startswith("data: "):
                        return _parse_space(json.loads(lines[i + 1][6:]))
        raise TimeoutError("Space API 超时")


def _parse_space(result):
    tags_str = result[0] or ""
    rating_data = result[1] if len(result) > 1 else {}
    chars_data = result[2] if len(result) > 2 else {}
    tags_data = result[3] if len(result) > 3 else {}

    tags_list = [t.strip() for t in tags_str.split(",") if t.strip()]

    # Handle LabelData format (label + confidences list)
    rating_label = rating_data.get("label", "?") if isinstance(rating_data, dict) else "?"
    rating_detail = rating_data.get("confidences", []) if isinstance(rating_data, dict) else []

    characters = []
    if isinstance(chars_data, dict):
        chars_label = chars_data.get("label", "")
        if chars_label:
            characters.append(chars_label)
        chars_confs = chars_data.get("confidences", [])
        for c in chars_confs:
            if isinstance(c, dict) and c.get("confidence", 0) > 0.5 and c.get("label"):
                characters.append(c["label"])
    elif isinstance(chars_data, str) and chars_data:
        characters = [chars_data]

    # Also extract high-confidence tags from tags_data confidences
    tag_details = []
    if isinstance(tags_data, dict) and "confidences" in tags_data:
        for c in tags_data["confidences"]:
            if isinstance(c, dict) and c.get("confidence", 0) > 0:
                tag_details.append({"label": c["label"], "confidence": c["confidence"]})

    return {
        "tags": tags_list,
        "rating": rating_label,
        "rating_detail": rating_detail,
        "characters": characters,
        "tag_details": tag_details,
        "source": "huggingface_space",
    }


# ── Colab API ──
def tag_colab(image_path, api_url, gen_thresh, char_thresh):
    """通过 Colab GPU API 打标。"""
    import io
    boundary = "----MinisFormBoundary"
    filename = os.path.basename(image_path)
    with open(image_path, "rb") as f:
        img_data = f.read()
    body = b""
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
    body += img_data
    body += f"\r\n--{boundary}--\r\n".encode()
    url = f"{api_url.rstrip('/')}/tag?gt={gen_thresh}&ct={char_thresh}"
    req = urllib.request.Request(url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    if "error" in data:
        raise RuntimeError(data["error"])
    data["source"] = "colab"
    return data


# ── 输出 ──
def format_text(data):
    lines = []
    lines.append("=== 评级 ===")
    if "rating_detail" in data and data["rating_detail"]:
        for item in data["rating_detail"]:
            if isinstance(item, dict):
                lines.append(f"  {item['label']}: {item['confidence']:.1%}")
    else:
        lines.append(f"  {data.get('rating', '?')}")

    chars = data.get("characters", [])
    if chars:
        lines.append(f"\n=== 角色 ===\n{', '.join(chars)}")

    # Show tag_details with confidence if available
    tag_details = data.get("tag_details", [])
    if tag_details:
        shown = [t for t in tag_details if t["confidence"] > 0.35]
        lines.append(f"\n=== 标签 ({len(shown)}个) ===")
        for t in shown:
            lines.append(f"  {t['label']} ({t['confidence']:.0%})")
    else:
        tags = data.get("tags", [])
        if tags:
            lines.append(f"\n=== 标签 ({len(tags)}个) ===\n{', '.join(tags)}")

    t = data.get("time")
    if t:
        lines.append(f"\n({t}s, {data.get('source', '?')})")
    return "\n".join(lines)


# ── CLI ──
def main():
    parser = argparse.ArgumentParser(description="wd-tagger: 给图片打 Danbooru 风格标签")
    parser.add_argument("image", help="图片路径")
    parser.add_argument("--api", choices=["space", "colab"], default="space",
                        help="API 后端 (默认 space)")
    parser.add_argument("--api-url", default=os.environ.get("WD_TAGGER_URL", ""),
                        help="Colab API 地址（需 --api colab，或设 WD_TAGGER_URL 环境变量）")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="模型（仅 space 模式）")
    parser.add_argument("--gen-threshold", type=float, default=0.35)
    parser.add_argument("--char-threshold", type=float, default=0.85)
    parser.add_argument("--use-mcut", action="store_true", help="MCut 自适应阈值（仅 space）")
    parser.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"错误: 图片不存在: {args.image}", file=sys.stderr)
        sys.exit(1)

    if args.api == "colab":
        if not args.api_url:
            print("错误: Colab 模式需要 --api-url 或设 WD_TAGGER_URL 环境变量", file=sys.stderr)
            sys.exit(1)
        result = tag_colab(args.image, args.api_url, args.gen_threshold, args.char_threshold)
    else:
        result = tag_space(args.image, args.model, args.gen_threshold, args.use_mcut, args.char_threshold)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text(result))


if __name__ == "__main__":
    main()
