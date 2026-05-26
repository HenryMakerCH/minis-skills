#!/usr/bin/env python3
"""Fetch tweets from X/Twitter user via internal GraphQL API.

Pure stdlib implementation. Requires TWITTER_AUTH_TOKEN and TWITTER_CT0
environment variables (Cookie values from a logged-in x.com session).

Usage:
    python3 fetch.py <screen_name> [--max N] [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

# QueryIds may rotate. If API returns empty instructions, refresh from:
# https://raw.githubusercontent.com/fa0311/twitter-openapi/refs/heads/main/src/config/placeholder.json
USER_BY_SCREEN_NAME_QUERY_ID = "IGgvgiOx4QZndDHuD3x9TQ"
USER_TWEETS_QUERY_ID = "36rb3Xj3iJ64Q-9wKDjCcQ"

BEARER_TOKEN = (
    "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs"
    "%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
)
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/133.0.0.0 Safari/537.36"
)

_SSL_CTX = ssl.create_default_context()


def _build_headers(auth_token: str, ct0: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "User-Agent": USER_AGENT,
        "x-csrf-token": ct0,
        "Cookie": f"auth_token={auth_token}; ct0={ct0}",
    }


def _fetch_json(url: str, headers: Dict[str, str], params: Dict[str, str]) -> Dict[str, Any]:
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(full_url, headers=headers)
    with urllib.request.urlopen(req, context=_SSL_CTX, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _get_user_id(screen_name: str, headers: Dict[str, str]) -> str:
    data = _fetch_json(
        f"https://api.x.com/graphql/{USER_BY_SCREEN_NAME_QUERY_ID}/UserByScreenName",
        headers,
        {
            "variables": json.dumps({"screen_name": screen_name}),
            "features": json.dumps({"responsive_web_graphql_timeline_navigation_enabled": True}),
            "fieldToggles": json.dumps({"withAuxiliaryUserLabels": False}),
        },
    )
    result = data.get("data", {}).get("user", {}).get("result", {})
    if not result:
        raise RuntimeError(f"User @{screen_name} not found")
    if result.get("__typename") == "UserUnavailable":
        reason = result.get("reason", "unknown")
        raise RuntimeError(f"User @{screen_name} unavailable: {reason}")
    return result["rest_id"]


def _get_user_tweets_raw(user_id: str, count: int, headers: Dict[str, str]) -> Dict[str, Any]:
    variables = {
        "userId": user_id,
        "count": min(count, 20),
        "includePromotedContent": True,
        "withQuickPromoteEligibilityTweetFields": True,
        "withVoice": True,
        "withV2Timeline": True,
    }
    features = {
        "responsive_web_graphql_exclude_directive_enabled": True,
        "verified_phone_label_enabled": False,
        "creator_subscriptions_tweet_preview_api_enabled": True,
        "responsive_web_graphql_timeline_navigation_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "c9s_tweet_anatomy_moderator_badge_enabled": True,
        "tweetypie_unmention_optimization_enabled": True,
        "responsive_web_edit_tweet_api_enabled": True,
        "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
        "view_counts_everywhere_api_enabled": True,
        "longform_notetweets_consumption_enabled": True,
        "responsive_web_twitter_article_tweet_consumption_enabled": True,
        "tweet_awards_web_tipping_enabled": False,
        "longform_notetweets_rich_text_read_enabled": True,
        "longform_notetweets_inline_media_enabled": True,
        "rweb_video_timestamps_enabled": True,
        "responsive_web_media_download_video_enabled": True,
        "freedom_of_speech_not_reach_fetch_enabled": True,
        "standardized_nudges_misinfo": True,
        "responsive_web_enhance_cards_enabled": False,
    }
    return _fetch_json(
        f"https://api.x.com/graphql/{USER_TWEETS_QUERY_ID}/UserTweets",
        headers,
        {"variables": json.dumps(variables), "features": json.dumps(features)},
    )


def _extract_tweet(entry: Dict[str, Any], screen_name: str) -> Optional[Dict[str, Any]]:
    entry_id = entry.get("entryId", "")
    if not entry_id.startswith("tweet-"):
        return None
    tweet = (
        entry.get("content", {})
        .get("itemContent", {})
        .get("tweet_results", {})
        .get("result", {})
    )
    if tweet.get("__typename") != "Tweet":
        return None
    note = tweet.get("note_tweet", {})
    if note and note.get("note_tweet_results"):
        text = note["note_tweet_results"]["result"].get("text", "")
    else:
        text = tweet.get("legacy", {}).get("full_text", "")
    legacy = tweet.get("legacy", {})
    return {
        "id": entry_id.replace("tweet-", ""),
        "screen_name": screen_name,
        "text": text,
        "created_at": legacy.get("created_at", ""),
        "metrics": {
            "likes": legacy.get("favorite_count", 0),
            "retweets": legacy.get("retweet_count", 0),
            "replies": legacy.get("reply_count", 0),
            "views": tweet.get("views", {}).get("count", "0"),
        },
    }


def _parse_timeline(data: Dict[str, Any], screen_name: str) -> List[Dict[str, Any]]:
    instructions = (
        data.get("data", {})
        .get("user", {})
        .get("result", {})
        .get("timeline", {})
        .get("timeline", {})
        .get("instructions", [])
    )
    tweets: List[Dict[str, Any]] = []
    for instr in instructions:
        if instr.get("type") != "TimelineAddEntries":
            continue
        for entry in instr.get("entries", []):
            t = _extract_tweet(entry, screen_name)
            if t:
                tweets.append(t)
    return tweets


def fetch_user_tweets(screen_name: str, count: int = 10) -> List[Dict[str, Any]]:
    """Fetch latest tweets from a user.

    Args:
        screen_name: Twitter handle without @
        count: Number of tweets (max 20)

    Returns:
        List of tweet dicts. See SKILL.md for schema.

    Raises:
        ValueError: If env vars are not set.
        RuntimeError: If user not found / unavailable.
    """
    auth_token = os.environ.get("TWITTER_AUTH_TOKEN")
    ct0 = os.environ.get("TWITTER_CT0")
    if not auth_token or not ct0:
        raise ValueError(
            "TWITTER_AUTH_TOKEN and TWITTER_CT0 must be set. "
            "See SKILL.md for how to obtain them."
        )
    headers = _build_headers(auth_token, ct0)
    user_id = _get_user_id(screen_name, headers)
    raw = _get_user_tweets_raw(user_id, count, headers)
    return _parse_timeline(raw, screen_name)[:count]


def _print_human(tweets: List[Dict[str, Any]], screen_name: str) -> None:
    print(f"@{screen_name} - latest {len(tweets)} tweet(s):\n")
    for i, t in enumerate(tweets, 1):
        dt = t["created_at"][:19] if t["created_at"] else "N/A"
        text = t["text"]
        if len(text) > 120:
            text = text[:120] + "..."
        m = t["metrics"]
        print(f"{i}. [{dt}]")
        print(f"   {text}")
        print(f"   ❤️{m['likes']} 🔁{m['retweets']} 💬{m['replies']} 👁{m['views']}")
        print()


def main() -> None:
    p = argparse.ArgumentParser(description="Fetch tweets from X/Twitter user")
    p.add_argument("screen_name", help="Twitter handle without @")
    p.add_argument("--max", type=int, default=10, help="Number of tweets (max 20, default 10)")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    args = p.parse_args()
    try:
        tweets = fetch_user_tweets(args.screen_name, count=args.max)
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        print(f"HTTP {e.code} {e.reason}: {body}", file=sys.stderr)
        sys.exit(2)
    if args.json:
        print(json.dumps(tweets, ensure_ascii=False, indent=2))
    else:
        _print_human(tweets, args.screen_name)


if __name__ == "__main__":
    main()
