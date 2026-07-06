#!/usr/bin/env python3
"""Remove exam posts and broken menus from practice channels."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from discord_channel_catalog import channel_mention, slug_from_name

GUILD_ID = "1519729833079210064"
PRACTICE_CHANNELS = ("spanish-practice", "french-practice")
BASE = "https://discord.com/api/v10"

DELETE_TITLES = {
    "About the DELE",
    "About the SIELE",
    "About the DELF",
    "About the DALF",
    "About the TCF",
    "Finding a test center (Spanish)",
    "Finding a test center (French)",
    "Find exam centers near you — pick your country",
}

DELETE_CONTENT_MARKERS = (
    "parlance-exam",
    "About the DELE",
    "About the SIELE",
    "Finding a test center",
)

PRACTICE_PIN = (
    "Writing practice only — share paragraphs here for feedback.\n"
    f"Exam info, tips, and finding a test center: **EXAMS** → {channel_mention('dele')}, "
    f"{channel_mention('delf')}, {channel_mention('find-a-seat')}."
)


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
    if any(m in content for m in DELETE_CONTENT_MARKERS):
        return True
    for emb in msg.get("embeds") or []:
        title = emb.get("title") or ""
        if title in DELETE_TITLES:
            return True
    if msg.get("components"):
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

    by_slug = {}
    for c in channels:
        if c.get("type") != 0:
            continue
        slug = slug_from_name(c.get("name", ""))
        if slug:
            by_slug[slug] = c["id"]

    for name in PRACTICE_CHANNELS:
        cid = by_slug.get(name)
        if not cid:
            print(f"skip #{name}")
            continue
        msgs = api("GET", f"/channels/{cid}/messages?limit=50")
        if not isinstance(msgs, list):
            print(f"error listing #{name}: {msgs}")
            continue
        deleted = 0
        has_pin = any(PRACTICE_PIN[:30] in (m.get("content") or "") for m in msgs)
        for msg in msgs:
            if not should_delete(msg):
                continue
            mid = msg["id"]
            r = api("DELETE", f"/channels/{cid}/messages/{mid}")
            if r.get("_status") and r.get("_status") != 204:
                print(f"  could not delete {mid} in #{name}: {r}")
            else:
                deleted += 1
                time.sleep(0.35)
        print(f"#{name}: removed {deleted} exam/menu message(s)")
        if not has_pin:
            time.sleep(0.5)
            api("POST", f"/channels/{cid}/messages", {"content": PRACTICE_PIN})
            print(f"  posted practice-only note in #{name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
