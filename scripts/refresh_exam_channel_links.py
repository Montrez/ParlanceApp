#!/usr/bin/env python3
"""Delete stale bot messages in exam channels and re-post with updated links."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from discord_channel_catalog import channel_name, slug_from_name
from discord_exam_data import EXAM_OVERVIEWS, EXAM_TIPS

GUILD_ID = "1519729833079210064"
BASE = "https://discord.com/api/v10"
DELAY = 0.6
EXAM_KEYS = ("dele", "siele", "delf", "dalf", "tcf")


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
            "User-Agent": "ParlanceExamSetup/1.0",
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


def pause() -> None:
    time.sleep(DELAY)


def get_bot_id() -> str:
    r = api("GET", "/users/@me")
    if isinstance(r, dict) and "id" in r:
        return r["id"]
    raise RuntimeError(f"Could not fetch bot user: {r}")


def delete_bot_messages(channel_id: str, bot_id: str) -> int:
    deleted = 0
    last_id: str | None = None
    while True:
        path = f"/channels/{channel_id}/messages?limit=50"
        if last_id:
            path += f"&before={last_id}"
        pause()
        msgs = api("GET", path)
        if not isinstance(msgs, list) or not msgs:
            break
        for m in msgs:
            if m.get("author", {}).get("id") == bot_id:
                pause()
                api("DELETE", f"/channels/{channel_id}/messages/{m['id']}")
                deleted += 1
        if len(msgs) < 50:
            break
        last_id = msgs[-1]["id"]
    return deleted


def main() -> int:
    if not os.environ.get("DISCORD_TOKEN"):
        print("Set DISCORD_TOKEN", file=sys.stderr)
        return 1

    bot_id = get_bot_id()
    print(f"Bot ID: {bot_id}")

    pause()
    channels = api("GET", f"/guilds/{GUILD_ID}/channels")
    if not isinstance(channels, list):
        print(f"Error fetching channels: {channels}", file=sys.stderr)
        return 1

    by_slug: dict[str, str] = {}
    for c in channels:
        if c.get("type") != 0:
            continue
        slug = slug_from_name(c.get("name", ""))
        if slug:
            by_slug[slug] = c["id"]

    for exam_key in EXAM_KEYS:
        cid = by_slug.get(exam_key)
        if not cid:
            print(f"  #{exam_key} not found, skipping")
            continue

        n = delete_bot_messages(cid, bot_id)
        print(f"  #{channel_name(exam_key)}: deleted {n} old bot message(s)")

        overview = EXAM_OVERVIEWS.get(exam_key, "")
        tips = EXAM_TIPS.get(exam_key, "")
        text = f"{overview}\n\n{tips}"
        pause()
        r = api("POST", f"/channels/{cid}/messages", {"content": text[:2000]})
        if "id" in r:
            print(f"  #{channel_name(exam_key)}: posted updated guide")
        else:
            print(f"  #{channel_name(exam_key)}: post error: {r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
