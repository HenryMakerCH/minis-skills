---
name: xai-imagine
description: 使用 xAI Imagine API 生成和编辑图片。文生图用 /v1/images/generations，图编辑用 /v1/images/edits。当用户说"xAI 生图"、"grok imagine"、"用 xAI 生成图片"、"用 xAI 编辑图片"、"改图"时触发。
version: 1.0.0
---

# xAI Imagine

调用 xAI Imagine API 进行图片生成和编辑。

## 前置条件

- 环境变量 `XAI_API_KEY` 已设置（Settings → Environment Variables）

## 用法

### 文生图

```bash
python3 /var/minis/skills/xai-imagine/scripts/imagine.py \
  --prompt "a red panda astronaut" \
  --output /var/minis/attachments/output.png
```

### 图编辑（核心功能）

```bash
python3 /var/minis/skills/xai-imagine/scripts/imagine.py \
  --edit \
  --input /path/to/source.jpg \
  --prompt "breast expansion" \
  --output /var/minis/attachments/output.png
```

### 参数

```
--edit              启用图编辑模式（/v1/images/edits），默认为文生图（/v1/images/generations）
--input FILE        源图片路径（图编辑模式必填）
--prompt TEXT       生成/编辑提示词
--output FILE       输出路径（默认 /var/minis/attachments/xai_imagine_output.png）
--model MODEL       模型选择（默认 grok-imagine-image）
                    可选：grok-imagine-image, grok-imagine-image-quality
--aspect RATIO      宽高比，如 1:1, 3:4, 4:3, 16:9, 9:16（文生图可用）
--resolution RES    分辨率：1k, 2k（默认 1k）
--n COUNT           生成数量（默认 1）
--format FORMAT     输出方式：file（保存文件）, url（打印URL）, b64（打印base64）
```

## 关键技术细节

### 两个端点，用途不同

| 操作 | 端点 | 说明 |
|------|------|------|
| 文生图 | `/v1/images/generations` | 纯文字生成新图 |
| 图编辑 | `/v1/images/edits` | 基于原图 + prompt 编辑 |

**重要**：图编辑必须用 `/v1/images/edits`，用 generations 端点传 image 会被忽略。

### image 对象格式

```json
{
  "image": {
    "url": "data:image/jpeg;base64,<base64数据>",
    "type": "image_url"
  }
}
```

`type: "image_url"` 字段**必须**，缺了会报 422。

### 内容审核

直接使用敏感 prompt（如 "breast expansion"）可能被拦截，但图编辑端点比文生图宽松。
若被 moderation 拒绝，返回错误提示让用户调整措辞。

### 模型选择

- `grok-imagine-image`：通用，支持二次元/动漫风格
- `grok-imagine-image-quality`：写实/照片风格优先，二次元效果差

## 注意事项

- API 返回临时 URL（imgen.x.ai），有效期有限，需及时下载保存
- 每张图 $0.02，图编辑计费包含输入+输出
- `response_format: "b64_json"` 可避免 URL 下载问题，但可能影响编辑效果
