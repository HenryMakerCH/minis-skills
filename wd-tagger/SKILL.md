---
name: wd-tagger
description: 调用 SmilingWolf wd-tagger（WaifuDiffusion Tagger）云端 API 给图片打 Danbooru 风格标签。当用户说"给这张图打标"、"识图出 tag"、"wd tagger"、"分析图片标签"、"这是什么图"（二次元/动漫图片）时触发。
version: 1.0.0
---

# WD Tagger

通过 HuggingFace Gradio API 调用 wd-tagger，传图返回 Danbooru 风格标签 + 分级 + 角色识别。

## ⚡ 快速用法

```bash
# 给一张图打标（自动上传 → 推理 → 输出标签）
python3 /var/minis/skills/wd-tagger/scripts/tag.py /path/to/image.png
```

## 脚本参数

```bash
python3 /var/minis/skills/wd-tagger/scripts/tag.py <图片路径> [选项]

选项:
  --model <名称>        模型（默认 wd-vit-tagger-v3）
  --gen-threshold <浮点> 通用标签阈值 (0-1, 默认 0.35)
  --char-threshold <浮点> 角色标签阈值 (0-1, 默认 0.35)
  --use-mcut             启用 MCut 自适应阈值
  --format <text|json>   输出格式（默认 text）

支持的模型:
  wd-swinv2-tagger-v3, wd-convnext-tagger-v3, wd-vit-tagger-v3 (推荐, 小/快)
  wd-vit-large-tagger-v3, wd-eva02-large-tagger-v3 (更大/更准)
  wd-v1-4-moat-tagger-v2, wd-v1-4-convnext-tagger-v2, wd-v1-4-vit-tagger-v2 (v2 旧版)
```

## 输出示例

```
=== 标签 ===
1girl, breasts, smile, blue_eyes, blonde_hair, school_uniform, ahoge

=== 评级 ===
general (98.4%)

=== 角色 ===
(无)
```

支持 `--format json` 输出机器可解析的结构化数据。
