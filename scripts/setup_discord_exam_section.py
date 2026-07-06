#!/usr/bin/env python3
"""Create EXAMS category and channels on Parlance Discord."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from discord_channel_catalog import CATEGORY_NAMES, channel_by_slug, channel_name, slug_from_name
from discord_exam_data import EXAM_OVERVIEWS, EXAM_TIPS, FIND_SEAT_INTRO, PASSED_INTRO

GUILD_ID = "1519729833079210064"
BASE = "https://discord.com/api/v10"
DELAY = 0.55

CHANNELS = [
    ("find-a-seat", "Role-based search for DELE, SIELE, DELF, DALF, TCF centers. Set exam + region roles first."),
    ("dele", "DELE prep, tips, and questions."),
    ("siele", "SIELE prep and questions."),
    ("delf", "DELF prep, tips, and questions."),
    ("dalf", "DALF prep and questions."),
    ("tcf", "TCF prep and questions."),
    ("passed", "Share when you pass — level, exam, and what helped."),
]


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


def pause():
    time.sleep(DELAY)


def main() -> int:
    if not os.environ.get("DISCORD_TOKEN"):
        print("Set DISCORD_TOKEN", file=sys.stderr)
        return 1

    channels = api("GET", f"/guilds/{GUILD_ID}/channels")
    if not isinstance(channels, list):
        print(channels, file=sys.stderr)
        return 1

    cat_id = None
    exam_cat_display = CATEGORY_NAMES["EXAMS"]
    for c in channels:
        if c.get("type") == 4 and c.get("name") in (exam_cat_display, "EXAMS"):
            cat_id = c["id"]
            print(f"Category {c['name']} exists")
            break
    if not cat_id:
        pause()
        cat = api("POST", f"/guilds/{GUILD_ID}/channels", {"name": exam_cat_display, "type": 4, "position": 3})
        if cat.get("_status"):
            print(f"Category error: {cat}", file=sys.stderr)
            return 1
        cat_id = cat["id"]
        print(f"Created category {exam_cat_display}")

    for i, (slug, topic) in enumerate(CHANNELS):
        if channel_by_slug(channels, slug):
            print(f"  #{channel_name(slug)} exists")
            continue
        pause()
        r = api(
            "POST",
            f"/guilds/{GUILD_ID}/channels",
            {"name": channel_name(slug), "type": 0, "parent_id": cat_id, "topic": topic, "position": i},
        )
        label = channel_name(slug)
        print(f"  Created #{label}" if "id" in r else f"  ERROR #{label}: {r}")

    pause()
    channels = api("GET", f"/guilds/{GUILD_ID}/channels")
    by_slug: dict[str, str] = {}
    if isinstance(channels, list):
        for c in channels:
            if c.get("type") != 0:
                continue
            slug = slug_from_name(c.get("name", ""))
            if slug:
                by_slug[slug] = c["id"]

    for exam_key in ("dele", "siele", "delf", "dalf", "tcf"):
        cid = by_slug.get(exam_key)
        if not cid:
            continue
        overview = EXAM_OVERVIEWS.get(exam_key, "")
        tips = EXAM_TIPS.get(exam_key, "")
        text = f"{overview}\n\n{tips}"
        pause()
        api("POST", f"/channels/{cid}/messages", {"content": text[:2000]})
        print(f"  Posted guide in #{channel_name(exam_key)}")

    if by_slug.get("find-a-seat"):
        pause()
        api("POST", f"/channels/{by_slug['find-a-seat']}/messages", {"content": FIND_SEAT_INTRO})
        print(f"  Posted intro in {channel_name('find-a-seat')}")

    if by_slug.get("passed"):
        pause()
        api("POST", f"/channels/{by_slug['passed']}/messages", {"content": PASSED_INTRO})
        print(f"  Posted intro in {channel_name('passed')}")

    print("\nRestart role bot: python3 scripts/discord_role_bot.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
