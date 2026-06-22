#!/usr/bin/env python3
"""Upload image to ComfyUI and run WD14Tagger, return tags."""

import sys
import json
import uuid
import time
import urllib.request
import urllib.error

COMFY = "http://192.168.2.200:8188"

def api_request(method, path, data=None, files=None):
    """Send request to ComfyUI API."""
    url = f"{COMFY}{path}"
    if files:
        # multipart upload
        import io
        boundary = "----FormBoundary" + uuid.uuid4().hex[:16]
        body = io.BytesIO()
        for field_name, (filename, filedata, content_type) in files.items():
            body.write(f"--{boundary}\r\n".encode())
            body.write(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode())
            body.write(f"Content-Type: {content_type}\r\n\r\n".encode())
            body.write(filedata)
            body.write(b"\r\n")
        body.write(f"--{boundary}--\r\n".encode())
        req = urllib.request.Request(url, data=body.getvalue(), method=method)
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    elif data is not None:
        req = urllib.request.Request(url, data=json.dumps(data).encode(), method=method)
        req.add_header("Content-Type", "application/json")
    else:
        req = urllib.request.Request(url, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        return None

def upload_image(filepath):
    """Upload image to ComfyUI, return filename."""
    import os
    filename = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        data = f.read()
    result = api_request("POST", "/api/upload/image", files={"image": (filename, data, "image/jpeg")})
    if result:
        return result.get("name") or result.get("filename") or filename
    return filename

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 comfy_wd_tagger.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]

    # Step 1: Upload image
    print(f"Uploading: {image_path}")
    img_name = upload_image(image_path)
    print(f"  Stored as: {img_name}")

    # Step 2: Create workflow
    # Node 1: LoadImage -> Node 2: WD14Tagger -> Node 3: SaveText
    workflow = {
        "1": {
            "inputs": {"image": img_name, "upload": "image"},
            "class_type": "LoadImage",
            "_meta": {"title": "Load Image"}
        },
        "2": {
            "inputs": {
                "image": ["1", 0],
                "model": "wd-eva02-large-tagger-v3",
                "threshold": 0.35,
                "character_threshold": 0.85,
                "replace_underscore": False,
                "trailing_comma": False,
                "exclude_tags": ""
            },
            "class_type": "WD14Tagger|pysssss",
            "_meta": {"title": "WD14 Tagger"}
        },
        "3": {
            "inputs": {
                "text": ["2", 0],
                "filename_prefix": "tags",
            },
            "class_type": "SaveText|pysssss",
            "_meta": {"title": "Save Tags"}
        }
    }

    # Step 3: Queue the prompt
    payload = {"prompt": workflow, "client_id": "minis_wd14"}
    result = api_request("POST", "/api/prompt", data=payload)
    if not result:
        print("Failed to queue prompt", file=sys.stderr)
        sys.exit(1)

    prompt_id = result.get("prompt_id")
    print(f"Prompt ID: {prompt_id}")

    # Step 4: Poll for result
    print("Waiting for result...")
    for i in range(60):
        time.sleep(2)
        history = api_request("GET", f"/api/history/{prompt_id}")
        if history and prompt_id in history:
            entry = history[prompt_id]
            status = entry.get("status", {})
            if status.get("completed") is not True:
                continue

            outputs = entry.get("outputs", {})
            for node_id, node_output in outputs.items():
                texts = node_output.get("text", [])
                if texts:
                    print("\n=== WD14 Tagger Result ===")
                    print(texts[0])
                    print("==========================")
                    return
            print("No text output in history:", json.dumps(outputs, indent=2)[:500])
            return

        if i % 5 == 0:
            q = api_request("GET", "/api/queue")
            if q:
                r = len(q.get("queue_running", []))
                p = len(q.get("queue_pending", []))
                print(f"  Queue: running={r}, pending={p}")

    print("Timeout waiting for result", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
