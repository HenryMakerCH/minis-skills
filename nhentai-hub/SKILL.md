---
name: nhentai-hub
description: Browse, search, download, and manage nhentai galleries via official API v2. Use when the user asks to search nhentai, look up a gallery, browse/favorites, download galleries, or anything related to nhentai. Trigger keywords: nhentai, NH, n站, 本子, doujinshi, gallery, 画廊.
version: 1.0.0
---
# nhentai-hub

Manage nhentai galleries via official API v2 (`/api/v2/docs`). Uses API Key auth via `Authorization: Key` header.

## Authentication

- `NHENTAI_API_KEY` — API key from nhentai account settings
- Falls back to the key from the user's saved environment variable

## Script

```
/var/minis/skills/nhentai-hub/scripts/nh.py
```

Alias:
```bash
alias nh="python3 /var/minis/skills/nhentai-hub/scripts/nh.py"
```

## Commands

### Search

```bash
python3 nh.py search "blue archive"                    # search, sorted by popular
python3 nh.py search "blue archive" --sort date        # sorted by date (newest)
python3 nh.py search "blue archive" --page 2           # page 2
python3 nh.py search "blue archive" --sort popular --page 1
```

### Browse galleries

```bash
python3 nh.py popular                                   # current popular
python3 nh.py popular --page 2                          # page 2
python3 nh.py random                                    # random gallery details
python3 nh.py browse                                    # browse all (newest)
python3 nh.py tagged --tag 128408                       # by tag ID (e.g. blue archive)
python3 nh.py tagged --tag 128408 --sort popular        # by tag sorted by popular
```

### Gallery details

```bash
python3 nh.py info 419630                               # full gallery info + tags + pages
python3 nh.py info 419630 --json                        # raw JSON output
python3 nh.py related 419630                            # related galleries
```

### Favorites (requires API key)

```bash
python3 nh.py favorites                                 # list favorites (page 1)
python3 nh.py favorites --page 2                        # page 2
python3 nh.py favorite 419630                           # check if favorited
python3 nh.py favorite 419630 --add                     # add to favorites
python3 nh.py favorite 419630 --remove                  # remove from favorites
python3 nh.py fav-random                                # random favorite
```

### Download

```bash
python3 nh.py download 419630                           # get download ZIP URL
python3 nh.py download 419630 --dir /tmp/nh             # download ZIP to dir
```

### Tags

```bash
python3 nh.py tagsearch "blue archive"                 # search tags by name
python3 nh.py tagids 832,3735,4068                     # get tag details by IDs
python3 nh.py tagtype parody                           # tags of type: parody, artist, character, tag, group, language, category
python3 nh.py tagtype parody blue-archive              # specific tag by type + slug
```

### User & Config

```bash
python3 nh.py user                                      # your account info
python3 nh.py blacklist                                 # view tag blacklist
python3 nh.py cdn                                       # CDN server list
```

### Image URLs

```bash
python3 nh.py pages 419630                              # print full image URLs for all pages
```

## Gallery object fields

```python
# Search/list result item:
id, media_id, english_title, japanese_title, thumbnail(str), tag_ids(list), num_pages, num_favorites, blacklisted

# Gallery detail (info):
id, media_id, title(dict: english/japanese/pretty), cover(dict: path/w/h), thumbnail(dict), scanlator, upload_date(unix), tags(list of dict), num_pages, num_favorites, pages(list of page dicts)

# Page:
number, path, width, height, thumbnail(path), thumbnail_width, thumbnail_height
```

## Image URL construction

```python
cdn = random.choice(["https://i1.nhentai.net", "https://i2.nhentai.net", ...])  # from /cdn
thumb = random.choice(["https://t1.nhentai.net", "https://t2.nhentai.net", ...])  # from /cdn

cover_url  = f"{cdn}/{cover['path']}"          # e.g. galleries/2323539/cover.jpg
page_url   = f"{cdn}/{page['path']}"           # e.g. galleries/2323539/1.jpg
thumb_url  = f"{thumb}/{page['thumbnail']}"    # e.g. galleries/2323539/1t.jpg
```

## Notes

- Search sorts: `popular` (default) or `date`
- Tag types: `artist`, `category`, `character`, `group`, `language`, `parody`, `tag`
- Rate limits are generous; treat 429 as a backoff signal
- Don't hardcode CDN subdomains — always fetch from `/api/v2/cdn`
- Download ZIP endpoint returns a signed URL, valid for a limited time
