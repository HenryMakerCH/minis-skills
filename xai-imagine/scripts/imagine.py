#!/usr/bin/env python3
"""
xAI Imagine API — 图片生成 & 图片编辑
用法: python3 imagine.py --help
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.request
import ssl


API_BASE = "https://api.x.ai/v1"
MODELS = ("grok-imagine-image", "grok-imagine-image-quality")


def get_api_key():
    key = os.environ.get("XAI_API_KEY", "")
    if not key:
        print("错误: 环境变量 XAI_API_KEY 未设置", file=sys.stderr)
        print("请在 Settings → Environment Variables 中添加 XAI_API_KEY", file=sys.stderr)
        sys.exit(1)
    return key


def api_request(endpoint, payload, api_key):
    """发送 JSON 请求到 xAI API，返回响应 dict"""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{API_BASE}{endpoint}",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=120)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"API 错误 [{e.code}]: {body}", file=sys.stderr)
        sys.exit(1)


def download_image(url, output_path):
    """用 curl 下载图片（urllib 对 imgen.x.ai 有 SSL 问题）"""
    result = subprocess.run(
        ["curl", "-k", "-s", "-o", output_path, "-w", "%{http_code}", url],
        capture_output=True, text=True, timeout=30,
    )
    if result.stdout.strip() != "200":
        print(f"下载失败: HTTP {result.stdout}", file=sys.stderr)
        sys.exit(1)


def read_image_b64(path):
    """读取图片文件并返回 base64 编码字符串"""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def guess_mime(path):
    ext = os.path.splitext(path)[1].lower()
    return {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(ext, "image/jpeg")


def do_generate(args, api_key):
    """文生图: /v1/images/generations"""
    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "n": args.n,
    }
    if args.aspect:
        payload["aspect_ratio"] = args.aspect
    if args.resolution:
        payload["resolution"] = args.resolution

    print(f"文生图: model={args.model}, prompt=\"{args.prompt}\"", file=sys.stderr)
    result = api_request("/images/generations", payload, api_key)
    return result


def do_edit(args, api_key):
    """图编辑: /v1/images/edits"""
    if not args.input:
        print("错误: 图编辑模式需要 --input 指定源图片", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.input):
        print(f"错误: 源图片不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    mime = guess_mime(args.input)
    img_b64 = read_image_b64(args.input)

    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "image": {
            "url": f"data:{mime};base64,{img_b64}",
            "type": "image_url",
        },
    }

    file_size = os.path.getsize(args.input)
    print(f"图编辑: model={args.model}, prompt=\"{args.prompt}\", "
          f"input={args.input} ({file_size} bytes)", file=sys.stderr)
    result = api_request("/images/edits", payload, api_key)
    return result


def save_output(result, args):
    """处理 API 返回，保存或打印输出"""
    if "data" not in result or not result["data"]:
        print(f"意外的 API 响应: {json.dumps(result)[:300]}", file=sys.stderr)
        sys.exit(1)

    items = result["data"]
    usage = result.get("usage", {})
    cost = usage.get("cost_in_usd_ticks", 0)
    if cost:
        print(f"费用: ${cost / 1e8:.2f}", file=sys.stderr)

    saved_paths = []
    for i, item in enumerate(items):
        url = item.get("url", "")
        b64 = item.get("b64_json") or item.get("b64", "")

        if args.format == "url":
            print(url)
            continue

        if args.format == "b64":
            if b64:
                print(b64)
            else:
                # URL 模式，需要下载后重新编码
                tmp = f"/tmp/xai_b64_{i}.tmp"
                download_image(url, tmp)
                with open(tmp, "rb") as f:
                    print(base64.b64encode(f.read()).decode())
                os.remove(tmp)
            continue

        # file 模式（默认）
        if len(items) == 1:
            out_path = args.output
        else:
            base, ext = os.path.splitext(args.output)
            out_path = f"{base}_{i}{ext}"

        if b64:
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(b64))
        elif url:
            download_image(url, out_path)
        else:
            print("响应中无图片数据", file=sys.stderr)
            sys.exit(1)

        size = os.path.getsize(out_path)
        print(f"已保存: {out_path} ({size} bytes)", file=sys.stderr)
        saved_paths.append(out_path)

    return saved_paths


def main():
    parser = argparse.ArgumentParser(
        description="xAI Imagine API — 图片生成 & 图片编辑"
    )
    parser.add_argument("--edit", action="store_true",
                        help="图编辑模式（/v1/images/edits）")
    parser.add_argument("--input", "-i",
                        help="源图片路径（图编辑模式必填）")
    parser.add_argument("--prompt", "-p", required=True,
                        help="生成/编辑提示词")
    parser.add_argument("--output", "-o",
                        default="/var/minis/attachments/xai_imagine_output.png",
                        help="输出路径")
    parser.add_argument("--model", "-m", default="grok-imagine-image",
                        choices=MODELS,
                        help="模型（默认 grok-imagine-image）")
    parser.add_argument("--aspect", "-a",
                        help="宽高比（如 1:1, 3:4, 16:9）")
    parser.add_argument("--resolution", "-r", default="1k",
                        choices=["1k", "2k"],
                        help="分辨率（默认 1k）")
    parser.add_argument("--n", type=int, default=1,
                        help="生成数量（默认 1）")
    parser.add_argument("--format", "-f", default="file",
                        choices=["file", "url", "b64"],
                        help="输出方式（默认 file）")

    args = parser.parse_args()
    api_key = get_api_key()

    if args.edit:
        result = do_edit(args, api_key)
    else:
        result = do_generate(args, api_key)

    paths = save_output(result, args)

    # 输出第一个文件路径供调用方使用
    if paths:
        print(paths[0])


if __name__ == "__main__":
    main()
