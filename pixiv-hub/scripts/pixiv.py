#!/usr/bin/env python3
"""Pixiv API CLI — pixivpy3 wrapper.

Auth: PIXIV_REFRESH_TOKEN env var or .pixiv_token file in script dir.
"""

import sys, os, json, time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN_FILE = SCRIPT_DIR / ".pixiv_token"

def get_token():
    tok = os.environ.get("PIXIV_REFRESH_TOKEN", "").strip()
    if tok:
        return tok
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    die("PIXIV_REFRESH_TOKEN not set. Set env var or create scripts/.pixiv_token")

def save_token(tok):
    TOKEN_FILE.write_text(tok + "\n")

def die(msg):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)

def get_api():
    from pixivpy3 import AppPixivAPI
    api = AppPixivAPI()
    api.auth(refresh_token=get_token())
    if api.refresh_token:
        save_token(api.refresh_token)
    return api

def pp(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))

# ── Commands ──────────────────────────────────────────────

def cmd_auth(_args):
    """Test authentication and print user info."""
    api = get_api()
    print(f"✅ Authenticated. user_id={api.user_id}")
    # Try to get user profile
    try:
        result = api.user_detail(api.user_id)
        if result and hasattr(result, 'profile') and result.profile:
            p = result.profile
            print(f"   Name: {p.name or '(unknown)'}")
            if hasattr(p, 'total_follow_users'):
                print(f"   Follows: {p.total_follow_users}")
    except Exception:
        pass

def cmd_ranking(args):
    """Usage: ranking [mode] [--limit N]
    Modes: day, week, month, week_rookie, day_male, day_female, day_r18, week_r18, week_r18g
    """
    mode = "day"
    limit = 10
    i = 0
    while i < len(args):
        if args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1]); i += 2
        elif not args[i].startswith("-"):
            mode = args[i]; i += 1
        else:
            i += 1
    api = get_api()
    result = api.illust_ranking(mode)
    illusts = result.illusts[:limit] if result and result.illusts else []
    print(f"📊 {mode} ranking ({len(illusts)} illusts):")
    for idx, w in enumerate(illusts, 1):
        tags = " ".join(f"#{t.name}" for t in (w.tags or [])[:4])
        print(f"  {idx:2d}. [{w.id}] {w.title}")
        print(f"      {w.user.name} | ❤{w.total_bookmarks} 👁{w.total_view}")
        print(f"      {tags}")

def cmd_search(args):
    """Usage: search <keyword> [--target partial|exact|title|tags] [--sort date|popular] [--page N] [--limit N] [--nsfw]"""
    if not args:
        die("search <keyword>")
    keyword = args[0]
    target = "partial_match_for_tags"
    sort = "date_desc"
    page = 1
    limit = 10
    nsfw = False
    i = 1
    while i < len(args):
        if args[i] == "--target" and i + 1 < len(args):
            target = args[i + 1]; i += 2
        elif args[i] == "--sort" and i + 1 < len(args):
            s = args[i + 1]
            sort = "popular_desc" if s.startswith("pop") else "date_desc"
            i += 2
        elif args[i] == "--page" and i + 1 < len(args):
            page = int(args[i + 1]); i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1]); i += 2
        elif args[i] == "--nsfw":
            nsfw = True; i += 1
        else:
            i += 1
    api = get_api()
    kwargs = dict(search_target=target, sort=sort, offset=(page - 1) * 30)
    if nsfw:
        kwargs["search_target"] = target
    result = api.search_illust(keyword, **kwargs)
    illusts = result.illusts[:limit] if result and result.illusts else []
    print(f"🔍 \"{keyword}\" ({target}, page {page}) — {len(illusts)} illusts:")
    for idx, w in enumerate(illusts, 1):
        tags = " ".join(f"#{t.name}" for t in (w.tags or [])[:5])
        print(f"  {idx:2d}. [{w.id}] {w.title}")
        print(f"      {w.user.name} | ❤{w.total_bookmarks} 👁{w.total_view} | {w.width}x{w.height}")
        print(f"      {tags}")

def cmd_bookmarks(args):
    """Usage: bookmarks [user_id] [--limit N]"""
    uid = None
    limit = 10
    i = 0
    while i < len(args):
        if args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1]); i += 2
        elif not args[i].startswith("-"):
            uid = int(args[i]); i += 1
        else:
            i += 1
    api = get_api()
    uid = uid or api.user_id
    result = api.user_bookmarks_illust(uid)
    illusts = result.illusts[:limit] if result and result.illusts else []
    print(f"⭐ User {uid} bookmarks ({len(illusts)} illusts):")
    for idx, w in enumerate(illusts, 1):
        print(f"  {idx:2d}. [{w.id}] {w.title}")
        print(f"      {w.user.name} | ❤{w.total_bookmarks}")

def cmd_following(args):
    """Usage: following [user_id] [--limit N]"""
    uid = None
    limit = 10
    i = 0
    while i < len(args):
        if args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1]); i += 2
        elif not args[i].startswith("-"):
            uid = int(args[i]); i += 1
        else:
            i += 1
    api = get_api()
    uid = uid or api.user_id
    result = api.user_following(uid)
    users = result.user_previews[:limit] if result and result.user_previews else []
    print(f"👥 User {uid} following ({len(users)} users):")
    for idx, u in enumerate(users, 1):
        print(f"  {idx:2d}. {u.user.name} (@{u.user.account})")
        if u.illusts:
            recent = ", ".join(f"[{i.id}]{i.title}" for i in u.illusts[:3])
            print(f"      Recent: {recent}")

def cmd_illust(args):
    """Usage: illust <id> [--json]"""
    if not args:
        die("illust <id>")
    illust_id = int(args[0])
    raw_json = "--json" in args
    api = get_api()
    result = api.illust_detail(illust_id)
    if not result or not result.illust:
        die(f"Illust {illust_id} not found")
    w = result.illust
    if raw_json:
        pp(result.illust)
        return
    print(f"🖼 {w.title}")
    print(f"   ID: {w.id}  |  {w.width}x{w.height}  |  {w.page_count} page(s)")
    print(f"   Author: {w.user.name} (@{w.user.account}, id:{w.user.id})")
    print(f"   ❤ {w.total_bookmarks}  👁 {w.total_view}")
    print(f"   Tags: {', '.join(t.name for t in (w.tags or []))}")
    if w.caption:
        cap = w.caption.replace('<br />', '\n').strip()[:300]
        print(f"   Caption: {cap}")
    if w.meta_single_page:
        print(f"   Original: {w.meta_single_page.original_image_url}")
    elif w.meta_pages:
        for j, p in enumerate(w.meta_pages[:10]):
            print(f"   [{j+1}] {p.image_urls.original}")
    print(f"   Page URL: https://www.pixiv.net/artworks/{w.id}")

def cmd_download(args):
    """Usage: download <id> [output_dir] [--limit N]"""
    if not args:
        die("download <id> [output_dir]")
    illust_id = int(args[0])
    out_dir = "."
    limit = 999
    i = 1
    while i < len(args):
        if args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1]); i += 2
        elif not args[i].startswith("-"):
            out_dir = args[i]; i += 1
        else:
            i += 1
    os.makedirs(out_dir, exist_ok=True)
    api = get_api()
    result = api.illust_detail(illust_id)
    if not result or not result.illust:
        die(f"Illust {illust_id} not found")
    w = result.illust
    saved = []
    if w.meta_single_page:
        url = w.meta_single_page.original_image_url
        fname = url.split("/")[-1]
        print(f"⬇️ {fname}")
        api.download(url, path=out_dir, fname=fname)
        saved.append(fname)
    elif w.meta_pages:
        for j, p in enumerate(w.meta_pages[:limit]):
            url = p.image_urls.original
            fname = url.split("/")[-1]
            print(f"⬇️ [{j+1}/{min(len(w.meta_pages), limit)}] {fname}")
            api.download(url, path=out_dir, fname=fname)
            saved.append(fname)
    print(f"✅ Downloaded {len(saved)} file(s) → {out_dir}/")

def cmd_related(args):
    """Usage: related <id> [--limit N]"""
    if not args:
        die("related <id>")
    illust_id = int(args[0])
    limit = 10
    if "--limit" in args:
        idx = args.index("--limit")
        limit = int(args[idx + 1])
    api = get_api()
    result = api.illust_related(illust_id)
    illusts = result.illusts[:limit] if result and result.illusts else []
    print(f"🔗 Related to {illust_id} ({len(illusts)} illusts):")
    for idx, w in enumerate(illusts, 1):
        print(f"  {idx:2d}. [{w.id}] {w.title}")
        print(f"      {w.user.name} | ❤{w.total_bookmarks}")

def cmd_user(args):
    """Usage: user <user_id> [--limit N]"""
    if not args:
        die("user <user_id>")
    uid = int(args[0])
    limit = 10
    if "--limit" in args:
        idx = args.index("--limit")
        limit = int(args[idx + 1])
    api = get_api()
    result = api.user_detail(uid)
    if not result or not hasattr(result, 'profile'):
        die(f"User {uid} not found")
    p = result.profile
    print(f"👤 {p.name} (@{p.account})")
    print(f"   ID: {uid}")
    if p.comment:
        print(f"   Bio: {p.comment[:200]}")
    if hasattr(p, 'total_follow_users'):
        print(f"   Following: {p.total_follow_users}")
    if hasattr(p, 'total_mypixiv_users'):
        print(f"   Pixiv Friends: {p.total_mypixiv_users}")
    # User works
    result2 = api.user_illusts(uid)
    illusts = result2.illusts[:limit] if result2 and result2.illusts else []
    if illusts:
        print(f"\n   Recent works ({len(illusts)}):")
        for idx, w in enumerate(illusts, 1):
            print(f"     {idx}. [{w.id}] {w.title} | ❤{w.total_bookmarks}")

def cmd_new(args):
    """Usage: new [--restrict public|private] [--limit N]"""
    restrict = "public"
    limit = 10
    i = 0
    while i < len(args):
        if args[i] == "--restrict" and i + 1 < len(args):
            restrict = args[i + 1]; i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1]); i += 2
        else:
            i += 1
    api = get_api()
    result = api.illust_follow(restrict=restrict)
    illusts = result.illusts[:limit] if result and result.illusts else []
    print(f"📰 Following feed ({restrict}, {len(illusts)} illusts):")
    for idx, w in enumerate(illusts, 1):
        print(f"  {idx:2d}. [{w.id}] {w.title}")
        print(f"      {w.user.name} | ❤{w.total_bookmarks}")

def cmd_trending(args):
    """Usage: trending [--tag <tag>] [--limit N]"""
    tag = None
    limit = 10
    i = 0
    while i < len(args):
        if args[i] == "--tag" and i + 1 < len(args):
            tag = args[i + 1]; i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1]); i += 2
        else:
            i += 1
    api = get_api()
    result = api.search_illust(tag or "", search_target="partial_match_for_tags", sort="popular_desc")
    illusts = result.illusts[:limit] if result and result.illusts else []
    label = f"trending: {tag}" if tag else "trending (popular)"
    print(f"🔥 {label} ({len(illusts)} illusts):")
    for idx, w in enumerate(illusts, 1):
        tags = " ".join(f"#{t.name}" for t in (w.tags or [])[:4])
        print(f"  {idx:2d}. [{w.id}] {w.title}")
        print(f"      {w.user.name} | ❤{w.total_bookmarks} 👁{w.total_view}")
        print(f"      {tags}")

def cmd_tag(args):
    """Usage: tag <tag_name> [--sort date|popular] [--page N] [--limit N]"""
    if not args:
        die("tag <tag_name>")
    tag_name = args[0]
    sort = "date_desc"
    page = 1
    limit = 10
    i = 1
    while i < len(args):
        if args[i] == "--sort" and i + 1 < len(args):
            s = args[i + 1]
            sort = "popular_desc" if s.startswith("pop") else "date_desc"
            i += 2
        elif args[i] == "--page" and i + 1 < len(args):
            page = int(args[i + 1]); i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1]); i += 2
        else:
            i += 1
    api = get_api()
    result = api.search_illust(tag_name, search_target="exact_match_for_tags", sort=sort, offset=(page - 1) * 30)
    illusts = result.illusts[:limit] if result and result.illusts else []
    print(f"🏷 #{tag_name} (page {page}, {len(illusts)} illusts):")
    for idx, w in enumerate(illusts, 1):
        print(f"  {idx:2d}. [{w.id}] {w.title}")
        print(f"      {w.user.name} | ❤{w.total_bookmarks} 👁{w.total_view}")

# ── Main ──────────────────────────────────────────────────

COMMANDS = {
    "auth": cmd_auth,
    "ranking": cmd_ranking,
    "search": cmd_search,
    "bookmarks": cmd_bookmarks,
    "following": cmd_following,
    "illust": cmd_illust,
    "download": cmd_download,
    "related": cmd_related,
    "user": cmd_user,
    "new": cmd_new,
    "trending": cmd_trending,
    "tag": cmd_tag,
}

USAGE = """pixiv.py — Pixiv API CLI

Usage: python3 pixiv.py <command> [args...]

Commands:
  auth                                    Test authentication
  ranking [mode] [--limit N]              Ranking (day|week|month|day_male|day_female|week_rookie|day_r18|week_r18)
  search <kw> [--target ...] [--sort ...] [--page N] [--limit N]
  tag <name> [--sort date|popular] [--page N] [--limit N]
  trending [--tag <tag>] [--limit N]      Popular illustrations
  bookmarks [uid] [--limit N]             User bookmarks
  following [uid] [--limit N]             User following list
  new [--restrict public|private] [--limit N]  Following feed (new posts)
  illust <id> [--json]                    Illust detail
  download <id> [dir] [--limit N]         Download original images
  related <id> [--limit N]                Related illustrations
  user <uid> [--limit N]                  User profile + recent works
"""

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(USAGE)
        return
    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"❌ Unknown command: {cmd}")
        print(USAGE)
        sys.exit(1)
    COMMANDS[cmd](sys.argv[2:])

if __name__ == "__main__":
    main()
