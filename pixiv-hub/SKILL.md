---
name: pixiv-hub
description: Browse, search, download Pixiv illustrations via pixivpy3. Use when the user asks about Pixiv, searching artwork, viewing rankings, downloading illustrations, checking bookmarks, or anything related to pixiv.net. Trigger keywords: pixiv, P站, p站, pixiv搜索, pixiv下载, 插画, 插图, 作品, illust.
version: 1.0.0
---
# pixiv-hub

Manage Pixiv illustrations via official mobile API (reverse-engineered). Uses `pixivpy3` library with OAuth refresh_token auth.

## Authentication

- `PIXIV_REFRESH_TOKEN` — OAuth refresh_token from PixEz app export or manual OAuth flow
- Falls back to `scripts/.pixiv_token` file if env var not set

## Script

```
/var/minis/skills/pixiv-hub/scripts/pixiv.py
```

## Commands

### Test Auth

```bash
python3 pixiv.py auth
```

### Ranking

```bash
python3 pixiv.py ranking                                # daily (default)
python3 pixiv.py ranking week                           # weekly
python3 pixiv.py ranking month                          # monthly
python3 pixiv.py ranking day_male --limit 20            # male preference, top 20
python3 pixiv.py ranking day_female                     # female preference
python3 pixiv.py ranking week_rookie                    # rookie ranking
python3 pixiv.py ranking day_r18                        # R-18 daily
python3 pixiv.py ranking week_r18                       # R-18 weekly
```

### Search

```bash
python3 pixiv.py search "初音ミク"                       # search by tag (partial match)
python3 pixiv.py search "初音ミク" --target exact        # exact tag match
python3 pixiv.py search "初音ミク" --target title        # title match
python3 pixiv.py search "初音ミク" --sort popular        # sorted by popularity
python3 pixiv.py search "初音ミク" --sort date --page 2  # newest, page 2
python3 pixiv.py search "初音ミク" --limit 20            # show 20 results
```

### Tag Browse

```bash
python3 pixiv.py tag "初音ミク"                          # exact tag, newest first
python3 pixiv.py tag "初音ミク" --sort popular           # sorted by popularity
python3 pixiv.py tag "初音ミク" --page 3 --limit 20      # page 3, 20 items
```

### Trending / Popular

```bash
python3 pixiv.py trending                               # overall popular
python3 pixiv.py trending --tag "ブルーアーカイブ"        # popular within tag
python3 pixiv.py trending --limit 20                    # top 20
```

### Illust Detail

```bash
python3 pixiv.py illust 123456789                       # show details
python3 pixiv.py illust 123456789 --json                 # raw JSON
```

### Download

```bash
python3 pixiv.py download 123456789                     # download to current dir
python3 pixiv.py download 123456789 /tmp/pixiv          # download to specific dir
python3 pixiv.py download 123456789 . --limit 5         # download max 5 pages
```

### User Profile & Works

```bash
python3 pixiv.py user 12345                             # user profile + recent works
python3 pixiv.py user 12345 --limit 20                  # show 20 recent works
```

### Bookmarks

```bash
python3 pixiv.py bookmarks                              # your bookmarks
python3 pixiv.py bookmarks 12345                        # another user's public bookmarks
python3 pixiv.py bookmarks --limit 30                   # 30 items
```

### Following Feed

```bash
python3 pixiv.py new                                    # new posts from followed users
python3 pixiv.py new --restrict private                 # private bookmarks feed
python3 pixiv.py new --limit 20                         # 20 items
```

### Following List

```bash
python3 pixiv.py following                              # who you follow
python3 pixiv.py following 12345                        # who user 12345 follows
```

### Related Illusts

```bash
python3 pixiv.py related 123456789                      # related works
python3 pixiv.py related 123456789 --limit 20           # 20 results
```

## Ranking Modes

| Mode | Description |
|------|-------------|
| `day` | Daily (default) |
| `week` | Weekly |
| `month` | Monthly |
| `week_rookie` | Weekly rookie |
| `day_male` | Male preference |
| `day_female` | Female preference |
| `day_r18` | Daily R-18 |
| `week_r18` | Weekly R-18 |
| `week_r18g` | Weekly R-18G |

## Search Targets

| Target | Description |
|--------|-------------|
| `partial_match_for_tags` | Partial tag match (default) |
| `exact_match_for_tags` | Exact tag match |
| `title_and_caption` | Title + caption |
| `title` | Title only (use via search) |
| `tags` | Tag only (use via `tag` command) |

## Notes

- Refresh token auto-renews on each auth; saved to `.pixiv_token`
- R-18 results require account settings to allow R-18 content
- Image URLs from pximg.net require Referer header for direct access
- Rate limiting exists but is generous for normal usage
- `search` with no specific target defaults to partial tag match
- `tag` command uses exact tag match for cleaner results
- `trending` is shorthand for `search --sort popular`
