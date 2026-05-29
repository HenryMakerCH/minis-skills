#!/usr/bin/env python3
"""nhentai API v2 CLI — browse, search, download, manage galleries."""
import os, sys, json, random, argparse
from urllib.request import Request, urlopen
from urllib.parse import urlencode

API = "https://nhentai.net/api/v2"
KEY = os.environ.get("NHENTAI_API_KEY", "")

def headers():
    h = {"User-Agent": "nhentai-hub/1.0 (Minis)"}
    if KEY:
        h["Authorization"] = f"Key {KEY}"
    return h

def req(path, method="GET", data=None):
    url = f"{API}{path}"
    body = json.dumps(data).encode() if data else None
    r = Request(url, data=body, headers=headers(), method=method)
    if data:
        r.add_header("Content-Type", "application/json")
    with urlopen(r) as resp:
        return json.loads(resp.read())

def fmt_gallery(g, compact=False):
    title = g.get("english_title") or g.get("japanese_title") or "?"
    if compact:
        fav = g.get("num_favorites", 0)
        return f"#{g['id']} {title[:60]} | {g.get('num_pages', '?')}p | ❤️{fav}"
    return title

def fmt_detail(d):
    t = d.get("title", {})
    lines = [
        f"#{d['id']} {t.get('english', '?')}",
        f"  Japanese: {t.get('japanese', '?')}",
        f"  Pages: {d['num_pages']} | ❤️ {d['num_favorites']}",
        f"  Upload: {d.get('upload_date', '?')} | Scanlator: {d.get('scanlator', '?')}",
    ]
    tags = d.get("tags", [])
    by_type = {}
    for tag in tags:
        by_type.setdefault(tag["type"], []).append(tag["name"])
    for ttype in ["parody", "character", "artist", "group", "category", "language", "tag"]:
        if ttype in by_type:
            lines.append(f"  [{ttype}] {', '.join(by_type[ttype][:8])}")
    return "\n".join(lines)

def print_list(results, total=None):
    if total is not None:
        print(f"Total: {total}\n")
    for g in results:
        print(fmt_gallery(g, compact=True))

# ── Commands ──────────────────────────────────────────────

def cmd_search(args):
    params = {"query": args.query, "page": args.page, "sort": args.sort}
    d = req(f"/search?{urlencode(params)}")
    print_list(d.get("result", []), d.get("total"))

def cmd_popular(args):
    results = req(f"/galleries/popular?page={args.page}")
    print_list(results)

def cmd_random(args):
    d = req("/galleries/random")
    # random returns just {"id": N}, fetch full details
    detail = req(f"/galleries/{d['id']}")
    print(fmt_detail(detail))
    if args.json:
        print(json.dumps(detail, indent=2))

def cmd_browse(args):
    d = req(f"/galleries?page={args.page}")
    print_list(d.get("result", []), d.get("total"))

def cmd_tagged(args):
    params = {"page": args.page, "sort": args.sort}
    d = req(f"/galleries/tagged?tag_id={args.tag}&{urlencode(params)}")
    print_list(d.get("result", []), d.get("total"))

def cmd_info(args):
    d = req(f"/galleries/{args.id}")
    print(fmt_detail(d))
    if args.json:
        print(json.dumps(d, indent=2))

def cmd_related(args):
    d = req(f"/galleries/{args.id}/related")
    if isinstance(d, list):
        print_list(d)
    elif isinstance(d, dict):
        print_list(d.get("result", []), d.get("total"))

def cmd_favorites(args):
    d = req(f"/favorites?page={args.page}")
    print_list(d.get("result", []), d.get("total"))

def cmd_favorite(args):
    if args.add:
        d = req(f"/galleries/{args.id}/favorite", method="POST")
        print(d)
    elif args.remove:
        d = req(f"/galleries/{args.id}/favorite", method="DELETE")
        print(d)
    else:
        d = req(f"/galleries/{args.id}/favorite")
        print(f"Favorited: {d.get('favorited')}")

def cmd_favrandom(args):
    d = req("/favorites/random")
    print(fmt_detail(d))

def cmd_user(args):
    d = req("/user")
    print(json.dumps(d, indent=2))

def cmd_blacklist(args):
    d = req("/blacklist")
    print(json.dumps(d, indent=2))

def cmd_cdn(args):
    d = req("/cdn")
    print(json.dumps(d, indent=2))

def cmd_download(args):
    d = req(f"/galleries/{args.id}/download", method="POST")
    url = d.get("url", "?")
    print(f"Download URL: {url}")
    if args.dir:
        os.makedirs(args.dir, exist_ok=True)
        import subprocess
        fname = f"nhentai_{args.id}.zip"
        fpath = os.path.join(args.dir, fname)
        print(f"Downloading to {fpath} ...")
        subprocess.run(["curl", "-sLo", fpath, url], check=True)
        print(f"Saved: {fpath} ({os.path.getsize(fpath) / 1024 / 1024:.1f} MB)")

def cmd_pages(args):
    d = req(f"/galleries/{args.id}")
    pages = d.get("pages", [])
    servers = req("/cdn")
    cdn = random.choice(servers["image_servers"])
    for p in pages:
        print(f"p{p['number']:03d}: {cdn}/{p['path']}")

def cmd_tagsearch(args):
    d = req("/tags/search", method="POST", data={"query": args.query, "type": args.type or None})
    if isinstance(d, list):
        for t in d:
            print(f"[{t['type']}] {t['name']} (slug={t['slug']}, count={t['count']})")
    else:
        print(d)

def cmd_tagids(args):
    ids = [i.strip() for i in args.ids.split(",")]
    d = req(f"/tags/ids?ids={','.join(ids)}")
    for t in d:
        print(f"[{t['type']}] {t['name']} (id={t['id']}, count={t['count']})")

def cmd_tagtype(args):
    if args.slug:
        d = req(f"/tags/{args.type}/{args.slug}")
        print(json.dumps(d, indent=2))
    else:
        d = req(f"/tags/{args.type}?page={args.page}")
        if isinstance(d, list):
            for t in d:
                print(f"{t['name']} (slug={t['slug']}, count={t['count']})")
        elif isinstance(d, dict):
            print_list(d.get("result", []), d.get("total"))

# ── Main ──────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="nhentai API v2 CLI")
    sp = p.add_subparsers(dest="cmd")

    # search
    sp_s = sp.add_parser("search")
    sp_s.add_argument("query")
    sp_s.add_argument("--sort", choices=["popular", "date"], default="popular")
    sp_s.add_argument("--page", type=int, default=1)

    # popular / random / browse
    sp_p = sp.add_parser("popular")
    sp_p.add_argument("--page", type=int, default=1)

    sp_r = sp.add_parser("random")
    sp_r.add_argument("--json", action="store_true")

    sp_b = sp.add_parser("browse")
    sp_b.add_argument("--page", type=int, default=1)

    # tagged
    sp_t = sp.add_parser("tagged")
    sp_t.add_argument("--tag", type=int, required=True)
    sp_t.add_argument("--sort", choices=["popular", "date"], default="popular")
    sp_t.add_argument("--page", type=int, default=1)

    # info / related
    sp_i = sp.add_parser("info")
    sp_i.add_argument("id", type=int)
    sp_i.add_argument("--json", action="store_true")

    sp_rel = sp.add_parser("related")
    sp_rel.add_argument("id", type=int)

    # favorites
    sp_f = sp.add_parser("favorites")
    sp_f.add_argument("--page", type=int, default=1)

    sp_fav = sp.add_parser("favorite")
    sp_fav.add_argument("id", type=int)
    sp_fav.add_argument("--add", action="store_true")
    sp_fav.add_argument("--remove", action="store_true")

    sp_fr = sp.add_parser("fav-random")

    # user / blacklist / cdn
    sp.add_parser("user")
    sp.add_parser("blacklist")
    sp.add_parser("cdn")

    # download
    sp_d = sp.add_parser("download")
    sp_d.add_argument("id", type=int)
    sp_d.add_argument("--dir")

    # pages
    sp_pg = sp.add_parser("pages")
    sp_pg.add_argument("id", type=int)

    # tags
    sp_ts = sp.add_parser("tagsearch")
    sp_ts.add_argument("query")
    sp_ts.add_argument("--type", choices=["artist","category","character","group","language","parody","tag"])
    sp_ti = sp.add_parser("tagids")
    sp_ti.add_argument("ids")
    sp_tt = sp.add_parser("tagtype")
    sp_tt.add_argument("type", choices=["artist","category","character","group","language","parody","tag"])
    sp_tt.add_argument("slug", nargs="?")
    sp_tt.add_argument("--page", type=int, default=1)

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return

    # API key check for private endpoints
    private = {"favorites", "favorite", "favrandom", "user", "blacklist", "download"}
    if args.cmd in private and not KEY:
        print("Error: NHENTAI_API_KEY not set. Set it in Settings → Environment Variables.")
        sys.exit(1)

    globals()[f"cmd_{args.cmd}"](args)

if __name__ == "__main__":
    main()
