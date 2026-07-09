#!/usr/bin/env python3
"""Create #daily-culture and pin an intro message."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from discord_channel_catalog import CATEGORY_NAMES, channel_name

GUILD_ID = "1519729833079210064"
BASE = "https://discord.com/api/v10"
SLUG = "daily-culture"
INTRO = """**Daily culture & language tips**

Morgan posts one tip here every morning around **10 AM Eastern** — false friends, register, interpreter craft, exam notes, and cultural context for Spanish and French.

Browse anytime. This channel is for reading and learning, not general chat."""


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
            "User-Agent": "ParlanceSetup/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
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

    name = channel_name(SLUG)
    channels = api("GET", f"/guilds/{GUILD_ID}/channels")
    if not isinstance(channels, list):
        print(f"Failed to list channels: {channels}", file=sys.stderr)
        return 1

    by_name = {c["name"]: c for c in channels if c.get("type") in (0, 4)}
    channel = by_name.get(name)
    community = by_name.get(CATEGORY_NAMES["COMMUNITY"])

    if not channel:
        payload = {
            "name": name,
            "type": 0,
            "topic": "Daily Spanish and French language, culture, and interpreter tips from Morgan.",
        }
        if community:
            payload["parent_id"] = community["id"]
        channel = api("POST", f"/guilds/{GUILD_ID}/channels", payload)
        if channel.get("_status"):
            print(f"ERROR creating #{name}: {channel}", file=sys.stderr)
            return 1
        print(f"Created #{name}")
    else:
        print(f"#{name} already exists")

    channel_id = channel["id"]
    msgs = api("GET", f"/channels/{channel_id}/messages?limit=10")
    has_intro = isinstance(msgs, list) and any(
        isinstance(m, dict) and "Daily culture & language tips" in m.get("content", "")
        for m in msgs
    )
    if not has_intro:
        msg = api("POST", f"/channels/{channel_id}/messages", {"content": INTRO})
        if msg.get("_status"):
            print(f"ERROR posting intro: {msg}", file=sys.stderr)
            return 1
        api("PUT", f"/channels/{channel_id}/pins/{msg['id']}")
        print("Posted and pinned intro")
    else:
        print("Intro already posted")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
