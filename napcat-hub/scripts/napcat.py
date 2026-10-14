#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NapCat / OneBot v11 HTTP API helper — pure stdlib, no dependencies.

Env:
  NAPCAT_BASE     base URL   (default http://bot.bg6hlq.cn:3043)
  NAPCAT_API_KEY  access token -> Authorization: Bearer <token>

Usage:
  napcat.py me                                  # 登录号信息
  napcat.py status                              # 在线状态
  napcat.py groups                              # 群列表（简表）
  napcat.py friends                             # 好友列表（简表）
  napcat.py members <group_id>                  # 群成员（简表）
  napcat.py group-info <group_id>
  napcat.py stranger <user_id>
  napcat.py send-group <group_id> <text|->
  napcat.py send-private <user_id> <text|->
  napcat.py send-group <group_id> <text> --at <user_id>   # 可重复
  napcat.py call <action> ['<json payload>']    # 任意 OneBot action
  napcat.py raw <action> ['<json>']             # 同 call，但打印完整 JSON

Flags:
  --raw        print full JSON instead of the condensed summary
  --json       same as --raw
  --base URL   override NAPCAT_BASE for this call
  text `-`     read message body from stdin (avoids shell quoting pain)
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = "http://bot.bg6hlq.cn:3043"


def _base(override=None):
    b = override or os.environ.get("NAPCAT_BASE") or DEFAULT_BASE
    return b.rstrip("/")


def call(action, payload=None, base=None, timeout=30):
    """POST an OneBot action; returns parsed JSON (or a synthetic error dict)."""
    url = "%s/%s" % (_base(base), action.lstrip("/"))
    body = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    token = os.environ.get("NAPCAT_API_KEY", "")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        return {"status": "failed", "retcode": e.code, "message": raw.strip(),
                "wording": "napcat http %s" % e.code}
    except Exception as e:  # noqa: BLE001
        return {"status": "failed", "retcode": -1,
                "message": "%s: %s" % (type(e).__name__, e),
                "wording": "transport error"}
    try:
        return json.loads(raw)
    except ValueError:
        return {"status": "failed", "retcode": -2, "message": raw[:400],
                "wording": "non-json response"}


def _ok(res):
    return res.get("status") == "ok" and res.get("retcode") == 0


def _fail(res):
    msg = res.get("message") or res.get("wording") or ""
    sys.stderr.write("ERROR retcode=%s %s\n" % (res.get("retcode"), msg))
    if "token verify failed" in str(msg):
        sys.stderr.write("hint: NAPCAT_API_KEY 不对，或没带 Authorization 头\n")
    return 1


def out(obj, raw=False, summarize=None):
    if raw or summarize is None:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    else:
        summarize(obj)


# ---------------------------------------------------------------- summaries

def s_me(res):
    d = res.get("data") or {}
    print("QQ %s (%s)" % (d.get("user_id"), d.get("nickname")))


def s_status(res):
    d = res.get("data") or {}
    print("online=%s good=%s" % (d.get("online"), d.get("good")))


def s_version(res):
    d = res.get("data") or {}
    print("%s  protocol=%s  version=%s" % (
        d.get("app_name"), d.get("protocol_version"), d.get("app_version")))


def s_groups(res):
    data = res.get("data") or []
    print("groups: %d" % len(data))
    for g in data:
        print("  %-12s %-28s %s/%s" % (g.get("group_id"), (g.get("group_name") or "")[:28],
                                       g.get("member_count"), g.get("max_member_count")))


def s_friends(res):
    data = res.get("data") or []
    print("friends: %d" % len(data))
    for f in data:
        remark = f.get("remark") or ""
        print("  %-12s %-20s %s" % (f.get("user_id"), (f.get("nickname") or "")[:20], remark))


def s_members(res):
    data = res.get("data") or []
    print("members: %d" % len(data))
    for m in data:
        name = m.get("card") or m.get("nickname") or ""
        print("  %-12s %-20s role=%-6s level=%s%s" % (
            m.get("user_id"), name[:20], m.get("role"), m.get("level"),
            " [BOT]" if m.get("is_robot") else ""))


def s_send(res):
    print("sent message_id=%s" % (res.get("data") or {}).get("message_id"))


# ---------------------------------------------------------------- commands

def cmd_send(kind, args, raw):
    if len(args) < 2:
        sys.stderr.write("usage: napcat.py send-%s <id> <text|-> [--at QQ ...]\n" % kind)
        return 2
    target = args[0]
    text = args[1]
    ats = []
    rest = args[2:]
    while rest:
        a = rest.pop(0)
        if a == "--at" and rest:
            ats.append(rest.pop(0))
        elif a.startswith("--at="):
            ats.append(a.split("=", 1)[1])
    if text == "-":
        text = sys.stdin.read()
    if ats:
        text = "".join("[CQ:at,qq=%s] " % q for q in ats) + text
    key = "group_id" if kind == "group" else "user_id"
    try:
        keyval = int(target)
    except ValueError:
        keyval = target
    action = "send_group_msg" if kind == "group" else "send_private_msg"
    res = call(action, {key: keyval, "message": text})
    if not _ok(res):
        return _fail(res)
    out(res, raw, s_send)
    return 0


def main(argv):
    raw = False
    base = None
    args = []
    it = iter(argv)
    for a in it:
        if a in ("--raw", "--json"):
            raw = True
        elif a == "--base":
            base = next(it, None)
        elif a.startswith("--base="):
            base = a.split("=", 1)[1]
        else:
            args.append(a)
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, rest = args[0], args[1:]

    if cmd in ("send-group", "send-private"):
        return cmd_send(cmd.split("-", 1)[1], rest, raw)

    if cmd == "call" or cmd == "raw":
        if not rest:
            sys.stderr.write("usage: napcat.py call <action> ['<json>']\n")
            return 2
        action = rest[0]
        payload = {}
        if len(rest) > 1 and rest[1] not in ("-",):
            try:
                payload = json.loads(rest[1])
            except ValueError as e:
                sys.stderr.write("bad json payload: %s\n" % e)
                return 2
        elif len(rest) > 1:
            payload = json.loads(sys.stdin.read() or "{}")
        res = call(action, payload, base=base)
        if not _ok(res):
            return _fail(res)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    table = {
        "me": ("get_login_info", {}, s_me),
        "login-info": ("get_login_info", {}, s_me),
        "status": ("get_status", {}, s_status),
        "version": ("get_version_info", {}, s_version),
        "groups": ("get_group_list", {}, s_groups),
        "friends": ("get_friend_list", {}, s_friends),
    }
    if cmd in table:
        action, payload, summ = table[cmd]
        res = call(action, payload, base=base)
        if not _ok(res):
            return _fail(res)
        out(res, raw, summ)
        return 0

    if cmd == "members":
        if not rest:
            sys.stderr.write("usage: napcat.py members <group_id>\n")
            return 2
        res = call("get_group_member_list", {"group_id": int(rest[0]), "no_cache": True}, base=base)
        if not _ok(res):
            return _fail(res)
        out(res, raw, s_members)
        return 0

    if cmd == "group-info":
        if not rest:
            sys.stderr.write("usage: napcat.py group-info <group_id>\n")
            return 2
        res = call("get_group_info", {"group_id": int(rest[0]), "no_cache": True}, base=base)
        if not _ok(res):
            return _fail(res)
        out(res, raw, None)
        return 0

    if cmd == "stranger":
        if not rest:
            sys.stderr.write("usage: napcat.py stranger <user_id>\n")
            return 2
        res = call("get_stranger_info", {"user_id": int(rest[0])}, base=base)
        if not _ok(res):
            return _fail(res)
        out(res, raw, None)
        return 0

    # bare action name fallback: `napcat.py get_group_list '{"group_id":1}'`
    payload = {}
    if rest:
        try:
            payload = json.loads(rest[0])
        except ValueError as e:
            sys.stderr.write("unknown command %r (%s)\n" % (cmd, e))
            return 2
    res = call(cmd, payload, base=base)
    if not _ok(res):
        return _fail(res)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
