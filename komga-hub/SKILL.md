---
name: komga-hub
description: Manage Komga manga library via REST API. Use when the user asks to query, update metadata, or manage manga books/series in their Komga server.
version: 1.0.0
---

# Komga Hub

通过 Komga REST API 管理漫画库（系列/书本元数据的读写）。

## 连接信息

- **地址**: `http://192.168.2.100:25600`
- **认证**: Header `X-API-Key: $KOMGA_KEY`（环境变量）
- **库根目录**: `/Erotics/Manga/`（WebDAV 路径）
- **Library ID**: `0QHXQNP8W612Q`

## 常用 API 端点

### 库（Libraries）
```bash
# 获取所有库
curl -s --noproxy "*" -H "X-API-Key: $KOMGA_KEY" "$KOMGA/api/v1/libraries"
```

### 系列（Series）
```bash
# 列出所有系列（分页，每页 size 条）
curl -s --noproxy "*" -H "X-API-Key: $KOMGA_KEY" "$KOMGA/api/v1/series?size=100"

# 获取单个系列详情
curl -s --noproxy "*" -H "X-API-Key: $KOMGA_KEY" "$KOMGA/api/v1/series/{seriesId}"

# 获取系列内书本
curl -s --noproxy "*" -H "X-API-Key: $KOMGA_KEY" "$KOMGA/api/v1/series/{seriesId}/books"

# 更新系列元数据（PATCH）
curl -s --noproxy "*" -X PATCH -H "X-API-Key: $KOMGA_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"新标题","summary":"简介","publisher":"出版社","status":"ENDED"}' \
  "$KOMGA/api/v1/series/{seriesId}/metadata"
```

### 书本（Books）
```bash
# 列出所有书本
curl -s --noproxy "*" -H "X-API-Key: $KOMGA_KEY" "$KOMGA/api/v1/books?size=100"

# 获取书本详情
curl -s --noproxy "*" -H "X-API-Key: $KOMGA_KEY" "$KOMGA/api/v1/books/{bookId}"

# 获取书本元数据
curl -s --noproxy "*" -H "X-API-Key: $KOMGA_KEY" "$KOMGA/api/v1/books/{bookId}/metadata"

# 更新书本元数据（PATCH）
curl -s --noproxy "*" -X PATCH -H "X-API-Key: $KOMGA_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"显示标题",
    "summary":"内容简介",
    "number":"1",
    "numberSort":1.0,
    "releaseDate":"2024-01-15",
    "authors":[{"name":"作者名","role":"writer"}],
    "tags":["tag1","tag2"],
    "isbn":"",
    "links":[{"label":"nhentai","url":"https://nhentai.net/g/123456/"}]
  }' \
  "$KOMGA/api/v1/books/{bookId}/metadata"

# 标记已读/未读
curl -s -X PUT -H "X-API-Key: $KOMGA_KEY" \
  "$KOMGA/api/v1/books/{bookId}/read-progress?progressCount=1&page=0"
```

### 强制扫描
```bash
# 触发库扫描
curl -s -X POST -H "X-API-Key: $KOMGA_KEY" \
  "$KOMGA/api/v1/libraries/{libraryId}/scan"
```

## 数据模型

### Series 元数据字段
| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 系列标题 |
| summary | string | 简介 |
| status | string | ONGOING / ENDED / ABANDONED / HIATUS |
| publisher | string | 出版社 |
| ageRating | null/int | 年龄分级 |
| language | string | 语言代码 (en/ja/zh) |
| genres | string[] | 体裁 |
| tags | string[] | 标签 |
| links | object[] | {label, url} 链接 |

### Book 元数据字段
| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 标题（覆盖文件名显示） |
| summary | string | 内容简介 |
| number | string | 卷号/话号 |
| numberSort | float | 排序用数字 |
| releaseDate | string/null | 发布日期 YYYY-MM-DD |
| authors | object[] | {name, role: writer/penciller/inker/colorist/letterer/cover} |
| tags | string[] | 标签列表 |
| links | object[] | {label, url} 外部链接 |
| isbn | string | ISBN |

## Python 使用示例

```python
import json, urllib.request

KOMGA = "http://192.168.2.100:25600"
KOMGA_KEY = "your-api-key"  # 从 os.environ["KOMGA_KEY"] 获取

def req(method, path, data=None):
    url = f"{KOMGA}{path}"
    headers = {"X-API-Key": KOMGA_KEY}
    body = json.dumps(data).encode() if data else None
    if data: headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read())

# 获取所有系列
series = req("GET", "/api/v1/series?size=100")
for s in series.get("content", []):
    print(f"{s['name']} ({s['booksCount']} books)")

# 更新书本元数据
req("PATCH", f"/api/v1/books/{book_id}/metadata", {
    "title": "显示标题",
    "summary": "简介",
    "authors": [{"name": "画家名", "role": "writer"}],
    "links": [{"label": "nhentai", "url": "https://nhentai.net/g/123456/"}]
})
```

## 触发词
- "Komga" / "漫画库" / "管理元数据" / "更新标签" / "扫描库"
- "查询系列" / "查书本" / "标已读" / "改标题"
