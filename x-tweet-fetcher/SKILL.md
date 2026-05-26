---
name: x-tweet-fetcher
description: 通过 X/Twitter 内部 GraphQL API 获取指定用户的最新推文。纯 Python 标准库实现，无第三方依赖，可移植到任何 Python 3.10+ 环境。使用 auth_token + ct0 Cookie 认证。当用户提到“获取 X 推文/Twitter 推文/X 用户推文/X 时间线”、“查看某个 X 账号最近发了什么”、“抓取 twitter.com 或 x.com 用户推文”、“fetch tweets/twitter timeline/x posts”、或想监控某个 X 账号的更新时触发。
version: 1.0.0
---

# x-tweet-fetcher

获取 X/Twitter 用户最新推文。零第三方依赖，单文件脚本。

## 认证

需要两个 Cookie 通过环境变量传入：

- `TWITTER_AUTH_TOKEN` — 登录凭证
- `TWITTER_CT0` — CSRF Token

### 在 Minis 环境获取 Cookie

```
browser_use navigate https://x.com         # 确认已登录
browser_use get_cookies       # 自动写入 offload env 文件
. /var/minis/offloads/env_cookies_xxx.sh   # 加载
export TWITTER_AUTH_TOKEN="$COOKIE_AUTH_TOKEN"
export TWITTER_CT0="$COOKIE_CT0"
```

### 在其他环境获取 Cookie

浏览器 DevTools → Application → Cookies → `https://x.com` → 复制 `auth_token` 和 `ct0` 的值。

## CLI 用法

```bash
# 默认 10 条
python3 scripts/fetch.py <screen_name>

# 指定数量（最多 20）
python3 scripts/fetch.py elonmusk --max 5

# JSON 输出（便于二次处理）
python3 scripts/fetch.py elonmusk --max 3 --json
```

## 作为库调用

```python
import os
from fetch import fetch_user_tweets

os.environ["TWITTER_AUTH_TOKEN"] = "..."
os.environ["TWITTER_CT0"] = "..."

tweets = fetch_user_tweets("elonmusk", count=10)
for t in tweets:
    print(f"{t['created_at']}: {t['text']}")
```

## 返回格式

```python
{
    "id": "1234567890",
    "screen_name": "elonmusk",
    "text": "推文正文",
    "created_at": "Wed May 20 05:27:40 +0000 2026",
    "metrics": {"likes": 4, "retweets": 0, "replies": 0, "views": "100"}
}
```

## 注意事项

- Cookie 过期需重新获取（通常数周至数月）
- API 风控：连续请求间建议 sleep 1-2 秒
- 只读操作（不会发推/点赞）
- 受保护账号（Protected）需要关注关系才能查看
- 如果 `queryId` 失效（API 返回空 instructions），从 https://raw.githubusercontent.com/fa0311/twitter-openapi/refs/heads/main/src/config/placeholder.json 获取最新 `UserTweets` queryId 并替换 `scripts/fetch.py` 中的 `USER_TWEETS_QUERY_ID` 常量
