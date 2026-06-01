---
name: wd-tagger
description: 调用 SmilingWolf wd-tagger（WaifuDiffusion Tagger）云端 API 给图片打 Danbooru 风格标签。当用户说"给这张图打标"、"识图出 tag"、"wd tagger"、"分析图片标签"、"这是什么图"（二次元/动漫图片）时触发。
version: 2.0.0
---

# WD Tagger

给图片打 Danbooru 风格标签，支持两个后端：

## 后端选择策略

| 场景 | 推荐后端 | 原因 |
|------|---------|------|
| **单张打标** | Space（默认） | 免费，无需配置，~10s/张 |
| **批量处理（≥2张）** | Colab GPU | ~0.2s/张，Space 逐张等太慢 |

批量时先设环境变量省去每次输 `--api-url`：

## ⚡ 快速用法

```bash
# HuggingFace Space（默认，免费，CPU ~10s）
python3 /var/minis/skills/wd-tagger/scripts/tag.py 图片.jpg

# Colab GPU API（快，<1s，需先启动 Colab）
python3 /var/minis/skills/wd-tagger/scripts/tag.py 图片.jpg --api colab --api-url https://xxx.ngrok-free.dev
```

设环境变量 `WD_TAGGER_URL` 后可省略 `--api-url`：

```bash
# 在 Settings → Environment Variables 设 WD_TAGGER_URL = Colab ngrok 地址
python3 /var/minis/skills/wd-tagger/scripts/tag.py 图片.jpg --api colab
```

## 参数

```
--api space|colab    后端选择（默认 space）
--api-url <URL>      Colab 地址
--gen-threshold F    通用标签阈值 (0-1, 默认 0.35)
--char-threshold F   角色标签阈值 (0-1, 默认 0.85)
--format text|json   输出格式
--model <模型>       Space 模式模型选择
--use-mcut           MCut 自适应阈值（仅 space）
```

## 输出示例

```
=== 评级 ===
general
  general: 64.2%
  sensitive: 51.8%

=== 角色 ===
plana_(blue_archive)

=== 标签 (28个) ===
1girl, solo, long_hair, looking_at_viewer, blush, ...

(0.18s, colab)
```
