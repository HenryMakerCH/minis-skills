---
name: wd-tagger
description: 调用 SmilingWolf wd-tagger（WaifuDiffusion Tagger）给图片打 Danbooru 风格标签。当用户说"给这张图打标"、"识图出 tag"、"wd tagger"、"分析图片标签"、"这是什么图"（二次元/动漫图片）时触发。
version: 3.0.0
---

# WD Tagger

给图片打 Danbooru 风格标签，支持三个后端：

## 后端选择策略

| 场景 | 推荐后端 | 原因 |
|------|---------|------|
| **首选（默认）** | ComfyUI 本地 | 局域网 P100 GPU，~3s/张，无需外网 |
| 备选 | Space（HuggingFace） | ComfyUI 不可用时兜底，免费 CPU ~10s |
| 批量（≥2张） | Colab GPU | ~0.2s/张 |

## 首选：ComfyUI 本地（推荐）

直接走局域网 ComfyUI 的 WD14Tagger 节点，无需任何配置。

### 用法

```bash
# 将图片上传到 ComfyUI → 跑 WD14Tagger → 输出标签
python3 /var/minis/skills/wd-tagger/scripts/comfy_tag.py <图片路径>
```

### 可调参数（在脚本中修改 workflow）
- `model`: wd-eva02-large-tagger-v3（默认）、wd-vit-tagger-v3、wd-swinv2-tagger-v3 等
- `threshold`: 通用标签阈值（默认 0.35）
- `character_threshold`: 角色标签阈值（默认 0.85）

### 依赖
- 局域网内 ComfyUI 运行中（192.168.2.200:8188）
- WD14Tagger 节点已安装（pysssss 插件）

## 备选：HuggingFace Space

ComfyUI 不可用时使用。

```bash
python3 /var/minis/skills/wd-tagger/scripts/tag.py 图片.jpg --api space
```

## 备选：Colab GPU

批量处理时使用，需先启动 Colab 并获取 ngrok 地址。

```bash
python3 /var/minis/skills/wd-tagger/scripts/tag.py 图片.jpg --api colab --api-url https://xxx.ngrok-free.dev
```

## 输出示例

```
=== WD14 Tagger Result ===
ibuki_(blue_archive), 1girl, solo, long_hair, breasts, blush, ...
```
