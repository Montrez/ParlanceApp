#!/usr/bin/env python3
"""Remove plain embed role menus from #choose-roles (keep v2 icon menus)."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from discord_channel_catalog import channel_by_slug, slug_from_name

GUILD_ID = "1519729833079210064"
BASE = "https://discord.com/api/v10"

DELETE_EMBED_TITLES = {"Introduce yourself", "Optional focus"}
KEEP_MARKERS = ("parlance-role-menus-v2", "parlance-roles-intro", "Pick your roles below")


def api(method: str, path: str, data: dict | None = None) -> dict | list:
    token = os.environ["DISCORD_TOKEN"]
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
            "User-Agent": "ParlanceCleanup/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            if resp.status == 204:
                return {}
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        try:
            payload = json.loads(err)
        except json.JSONDecodeError:
            payload = {"message": err}
        payload["_status"] = e.code
        return payload


def should_delete(msg: dict) -> bool:
    content = msg.get("content") or ""
    if any(m in content for m in KEEP_MARKERS):
        return False
    for emb in msg.get("embeds") or []:
        if emb.get("title") in DELETE_EMBED_TITLES:
            return True
    return False


def main() -> int:
    if not os.environ.get("DISCORD_TOKEN"):
        print("Set DISCORD_TOKEN", file=sys.stderr)
        return 1

    channels = api("GET", f"/guilds/{GUILD_ID}/channels")
    if not isinstance(channels, list):
        print(channels, file=sys.stderr)
        return 1

    choose = channel_by_slug(channels, "choose-roles")
    if not choose:
        print("choose-roles channel not found", file=sys.stderr)
        return 1

    cid = choose["id"]
    msgs = api("GET", f"/channels/{cid}/messages?limit=50")
    if not isinstance(msgs, list):
        print(msgs, file=sys.stderr)
        return 1

    deleted = 0
    for msg in msgs:
        if not should_delete(msg):
            continue
        r = api("DELETE", f"/channels/{cid}/messages/{msg['id']}")
        if r.get("_status") and r.get("_status") != 204:
            print(f"  could not delete {msg['id']}: {r}")
        else:
            deleted += 1
            title = (msg.get("embeds") or [{}])[0].get("title", "?")
            print(f"  removed: {title}")
            time.sleep(0.35)

    print(f"Removed {deleted} plain embed menu(s) from #{slug_from_name(choose.get('name', 'choose-roles'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
