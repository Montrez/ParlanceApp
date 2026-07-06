#!/usr/bin/env python3
"""Apply emoji channel and category names on Parlance Discord."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from discord_channel_catalog import CATEGORY_NAMES, CHANNEL_NAMES, slug_from_name

GUILD_ID = "1519729833079210064"
BASE = "https://discord.com/api/v10"
DELAY = 0.55


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
            "User-Agent": "ParlanceRename/1.0",
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


def main() -> int:
    if not os.environ.get("DISCORD_TOKEN"):
        print("Set DISCORD_TOKEN", file=sys.stderr)
        return 1

    channels = api("GET", f"/guilds/{GUILD_ID}/channels")
    if not isinstance(channels, list):
        print(channels, file=sys.stderr)
        return 1

    renamed = 0
    for ch in channels:
        cid = ch["id"]
        old = ch.get("name", "")
        ctype = ch.get("type")

        if ctype == 4:
            target = CATEGORY_NAMES.get(old)
            if not target and old in CATEGORY_NAMES.values():
                continue
            if not target:
                for slug, display in CATEGORY_NAMES.items():
                    if old.upper() == slug or old == slug:
                        target = display
                        break
        elif ctype == 0:
            slug = slug_from_name(old)
            if not slug:
                continue
            target = CHANNEL_NAMES[slug]
        else:
            continue

        if not target or old == target:
            print(f"  ok: {old}")
            continue

        time.sleep(DELAY)
        r = api("PATCH", f"/channels/{cid}", {"name": target})
        if r.get("_status"):
            print(f"  ERROR {old} → {target}: {r}")
        else:
            print(f"  {old} → {target}")
            renamed += 1

    print(f"\nRenamed {renamed} channel(s)/categor(ies).")
    print("Restart discord_role_bot.py if it is running.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
