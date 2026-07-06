#!/usr/bin/env python3
"""Post channel welcome copy (human tone, no bot callouts)."""
from __future__ import annotations

import json
import os
import sys
import urllib.request

GUILD_ID = "1519729833079210064"
BASE = "https://discord.com/api/v10"

INTROS = {
    "support": (
        "Questions about Parlance, Coach, sign-in, or exams? Ask here — "
        "someone from the community or the team will point you in the right direction."
    ),
    "general": (
        "General chat for Parlance users and anyone working toward interpreter-level writing."
    ),
    "bugs": (
        "Something broken? Describe what happened, your device, and the app version. "
        "The more specific you are, the faster we can fix it."
    ),
    "feedback": (
        "Ideas for Parlance — what would help your practice or exam prep? "
        "One clear sentence about what you want goes a long way."
    ),
    "announcements": (
        "Release notes and news about Parlance. Check here for TestFlight builds and updates."
    ),
}


def api(method: str, path: str, data: dict | None = None) -> dict | list:
    token = os.environ["DISCORD_TOKEN"]
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=body,
        method=method,
        headers={"Authorization": f"Bot {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def main() -> int:
    if not os.environ.get("DISCORD_TOKEN"):
        print("Set DISCORD_TOKEN", file=sys.stderr)
        return 1
    channels = api("GET", f"/guilds/{GUILD_ID}/channels")
    by_name = {c["name"]: c["id"] for c in channels if c.get("type") == 0}
    for name, text in INTROS.items():
        cid = by_name.get(name)
        if not cid:
            print(f"  skip #{name}")
            continue
        api("POST", f"/channels/{cid}/messages", {"content": text})
        print(f"  posted in #{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
