#!/usr/bin/env python3
"""
Reorganize Parlance Discord channels by language.

Before:
  ✍️ PRACTICE  → spanish-practice, french-practice
  🎯 EXAMS     → find-a-seat, dele, siele, delf, dalf, tcf, passed

After:
  🇪🇸 ESPAÑOL  → spanish-practice, dele, siele
  🇫🇷 FRANÇAIS → french-practice, delf, dalf, tcf
  🎯 EXAMS     → find-a-seat, passed
  (old PRACTICE category deleted once empty)
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from discord_channel_catalog import CATEGORY_NAMES, channel_name, slug_from_name

GUILD_ID = "1519729833079210064"
BASE = "https://discord.com/api/v10"
DELAY = 0.6

SPANISH_SLUGS = ["spanish-practice", "dele", "siele"]
FRENCH_SLUGS  = ["french-practice", "delf", "dalf", "tcf"]
EXAMS_SLUGS   = ["find-a-seat", "passed"]

SPANISH_CAT = CATEGORY_NAMES["SPANISH"]   # 🇪🇸 ESPAÑOL
FRENCH_CAT  = CATEGORY_NAMES["FRENCH"]    # 🇫🇷 FRANÇAIS
EXAMS_CAT   = CATEGORY_NAMES["EXAMS"]     # 🎯 EXAMS
OLD_PRACTICE_NAMES = {"✍️ PRACTICE", "PRACTICE"}


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
            "User-Agent": "ParlanceReorg/1.0",
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


def get_or_create_category(channels: list[dict], name: str, position: int) -> str:
    for c in channels:
        if c.get("type") == 4 and c.get("name") == name:
            print(f"  Category '{name}' already exists")
            return c["id"]
    pause()
    r = api("POST", f"/guilds/{GUILD_ID}/channels", {
        "name": name, "type": 4, "position": position
    })
    if r.get("_status"):
        raise RuntimeError(f"Failed to create category '{name}': {r}")
    print(f"  Created category '{name}'")
    return r["id"]


def move_channel(channel_id: str, parent_id: str, position: int, slug: str) -> None:
    pause()
    r = api("PATCH", f"/channels/{channel_id}", {
        "parent_id": parent_id,
        "position": position,
    })
    if r.get("_status"):
        print(f"    ERROR moving #{channel_name(slug)}: {r}")
    else:
        print(f"    Moved #{channel_name(slug)} ✓")


def main() -> int:
    if not os.environ.get("DISCORD_TOKEN"):
        print("Set DISCORD_TOKEN", file=sys.stderr)
        return 1

    channels = api("GET", f"/guilds/{GUILD_ID}/channels")
    if not isinstance(channels, list):
        print(f"Error fetching channels: {channels}", file=sys.stderr)
        return 1

    # Find positions of existing categories to place new ones sensibly
    cat_positions: dict[str, int] = {
        c["name"]: c.get("position", 99)
        for c in channels if c.get("type") == 4
    }
    practice_pos = cat_positions.get("✍️ PRACTICE", cat_positions.get("PRACTICE", 5))

    print("Creating language categories...")
    spanish_id = get_or_create_category(channels, SPANISH_CAT, practice_pos)
    pause()
    channels = api("GET", f"/guilds/{GUILD_ID}/channels")  # refresh
    french_id  = get_or_create_category(channels, FRENCH_CAT,  practice_pos + 1)

    pause()
    channels = api("GET", f"/guilds/{GUILD_ID}/channels")  # refresh after possible creation

    # Index text channels by slug
    by_slug: dict[str, dict] = {}
    for c in channels:
        if c.get("type") != 0:
            continue
        slug = slug_from_name(c.get("name", ""))
        if slug:
            by_slug[slug] = c

    # Find the EXAMS category id
    exams_id: str | None = None
    for c in channels:
        if c.get("type") == 4 and c.get("name") == EXAMS_CAT:
            exams_id = c["id"]
            break

    print(f"\nMoving Spanish channels to '{SPANISH_CAT}'...")
    for i, slug in enumerate(SPANISH_SLUGS):
        ch = by_slug.get(slug)
        if ch:
            move_channel(ch["id"], spanish_id, i, slug)
        else:
            print(f"    #{channel_name(slug)} not found, skipping")

    print(f"\nMoving French channels to '{FRENCH_CAT}'...")
    for i, slug in enumerate(FRENCH_SLUGS):
        ch = by_slug.get(slug)
        if ch:
            move_channel(ch["id"], french_id, i, slug)
        else:
            print(f"    #{channel_name(slug)} not found, skipping")

    if exams_id:
        print(f"\nEnsuring find-a-seat and passed stay in '{EXAMS_CAT}'...")
        for i, slug in enumerate(EXAMS_SLUGS):
            ch = by_slug.get(slug)
            if ch and ch.get("parent_id") != exams_id:
                move_channel(ch["id"], exams_id, i, slug)
            elif ch:
                print(f"    #{channel_name(slug)} already in EXAMS ✓")
    else:
        print(f"\nWARN: '{EXAMS_CAT}' category not found — find-a-seat/passed not moved")

    # Delete old PRACTICE category if it's now empty
    pause()
    channels = api("GET", f"/guilds/{GUILD_ID}/channels")
    if isinstance(channels, list):
        for c in channels:
            if c.get("type") == 4 and c.get("name") in OLD_PRACTICE_NAMES:
                children = [x for x in channels if x.get("parent_id") == c["id"]]
                if not children:
                    pause()
                    api("DELETE", f"/channels/{c['id']}")
                    print(f"\nDeleted empty category '{c['name']}'")
                else:
                    print(f"\nWARN: '{c['name']}' still has {len(children)} channel(s) — not deleted")

    print("\nDone. Channel layout reorganized by language.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
