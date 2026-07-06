#!/usr/bin/env python3
"""Organize Parlance Discord: description, categories, channel layout, roles."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from discord_channel_catalog import CATEGORY_NAMES, channel_by_slug, channel_name

GUILD_ID = "1519729833079210064"
BASE = "https://discord.com/api/v10"
DELAY = 0.6

DESCRIPTION = (
    "A language writing journal for aspiring interpreters. "
    "Practice Spanish and French with structured AI feedback, "
    "exam prep (DELE/DELF), and a community of serious language learners."
)

CATEGORIES = [
    ("WELCOME", ["rules", "announcements"]),
    ("COMMUNITY", ["general", "introductions"]),
    ("PRODUCT", ["support", "feedback", "bugs", "beta-testers", "parlance-coach"]),
    ("PRACTICE", ["spanish-practice", "french-practice"]),
]

ROLES = [
    ("Beta Tester", 0x5865F2, True),
    ("Spanish", 0xE67E22, False),
    ("French", 0x3498DB, False),
    ("DELE / DELF", 0x9B59B6, False),
    ("Contributor", 0x2ECC71, False),
]

RULES_MESSAGE = """**Parlance Community Rules**

1. **Be respectful** — critique writing, not people.
2. **Stay on topic** — this server is for language writing practice and Parlance the app.
3. **No spam** — no unsolicited ads, repeated self-promo, or off-topic floods.
4. **Practice languages in the right channels** — Spanish in #spanish-practice, French in #french-practice.
5. **Support & bugs** — use #support and #bugs so we can help you faster.
6. **Privacy** — don't share others' writing without permission.

Questions? Ask in #support. Welcome to Parlance."""


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


def pause():
    time.sleep(DELAY)


def main() -> int:
    if not os.environ.get("DISCORD_TOKEN"):
        print("Set DISCORD_TOKEN", file=sys.stderr)
        return 1

    print("Setting server description...")
    r = api("PATCH", f"/guilds/{GUILD_ID}", {"description": DESCRIPTION})
    if r.get("_status") == 403:
        print("  SKIP description — bot needs Manage Server permission")
    elif r.get("_status"):
        print(f"  ERROR: {r}")
    else:
        print("  OK")

    pause()
    channels = api("GET", f"/guilds/{GUILD_ID}/channels")
    if not isinstance(channels, list):
        print(f"Failed to list channels: {channels}", file=sys.stderr)
        return 1

    by_name = {c["name"]: c for c in channels if c.get("type") in (0, 2, 4)}
    for slug, display in CATEGORY_NAMES.items():
        if slug in by_name and display not in by_name:
            by_name[display] = by_name[slug]

    print("Creating categories and organizing channels...")
    pos = 0
    for cat_slug, channel_slugs in CATEGORIES:
        cat_display = CATEGORY_NAMES[cat_slug]
        pause()
        cat = by_name.get(cat_display) or by_name.get(cat_slug)
        if not cat:
            cat = api("POST", f"/guilds/{GUILD_ID}/channels", {"name": cat_display, "type": 4, "position": pos})
        else:
            pause()
            cat = api("PATCH", f"/channels/{cat['id']}", {"name": cat_display, "position": pos})
        if cat.get("_status"):
            print(f"  ERROR category {cat_display}: {cat}")
            continue
        cat_id = cat["id"]
        print(f"  Category: {cat_display}")
        pos += 1
        for i, ch_slug in enumerate(channel_slugs):
            ch = channel_by_slug(list(by_name.values()), ch_slug) or by_name.get(channel_name(ch_slug)) or by_name.get(ch_slug)
            if not ch:
                print(f"    missing #{channel_name(ch_slug)}")
                continue
            pause()
            upd = api("PATCH", f"/channels/{ch['id']}", {"parent_id": cat_id, "position": i, "name": channel_name(ch_slug)})
            if upd.get("_status"):
                print(f"    ERROR moving #{channel_name(ch_slug)}: {upd}")
            else:
                print(f"    #{channel_name(ch_slug)} → {cat_display}")

    print("Creating roles...")
    existing_roles = api("GET", f"/guilds/{GUILD_ID}/roles")
    existing_names = set()
    if isinstance(existing_roles, list):
        existing_names = {r["name"] for r in existing_roles}

    for name, color, hoist in ROLES:
        if name in existing_names:
            print(f"  Role exists: {name}")
            continue
        pause()
        r = api(
            "POST",
            f"/guilds/{GUILD_ID}/roles",
            {"name": name, "color": color, "hoist": hoist, "mentionable": True},
        )
        if r.get("_status") == 403:
            print("  SKIP roles — bot needs Manage Roles permission")
            break
        if r.get("_status"):
            print(f"  ERROR role {name}: {r}")
        else:
            print(f"  Created role: {name}")

    rules = channel_by_slug(list(by_name.values()), "rules") or by_name.get("rules")
    if rules:
        pause()
        msgs = api("GET", f"/channels/{rules['id']}/messages?limit=5")
        has_rules = isinstance(msgs, list) and any(
            isinstance(m, dict) and "Parlance Community Rules" in m.get("content", "")
            for m in msgs
        )
        if not has_rules:
            r = api("POST", f"/channels/{rules['id']}/messages", {"content": RULES_MESSAGE})
            if r.get("_status"):
                print(f"Rules post error: {r}")
            else:
                print("Posted rules in #rules")
        else:
            print("Rules already posted in #rules")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
