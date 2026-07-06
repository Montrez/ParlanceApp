#!/usr/bin/env python3
"""Sync Parlance Discord roles (plain names) and channel topic."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from discord_channel_catalog import channel_by_slug, channel_name
from discord_role_catalog import ROLES

GUILD_ID = "1519729833079210064"
BOT_ROLE_ID = "1519738151025770529"  # Parlance bot role — update if you reset the bot
WELCOME_CAT = "1519739260893134940"
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
            "User-Agent": "ParlanceRoleSetup/2.0",
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


def lock_choose_roles_channel(channel_id: str) -> None:
    """Members can read and use menus; only the bot can post."""
    deny = str(2048 + 262144 + 524288 + 4194304)  # no send / threads
    allow_everyone = str(1024 + 65536)  # view + history
    allow_bot = str(1024 + 2048 + 65536 + 3072)  # view, send, history, embed, attach
    pause()
    r = api(
        "PATCH",
        f"/channels/{channel_id}",
        {
            "permission_overwrites": [
                {"id": GUILD_ID, "type": 0, "allow": allow_everyone, "deny": deny},
                {"id": BOT_ROLE_ID, "type": 0, "allow": allow_bot, "deny": "0"},
            ]
        },
    )
    if r.get("_status"):
        print(f"  WARN: could not lock #choose-roles: {r}")
    else:
        print("  Locked #choose-roles (menus only, no chatting)")


def sync_roles() -> None:
    if not isinstance(roles, list):
        print(f"Failed to list roles: {roles}", file=sys.stderr)
        return
    by_name = {r["name"]: r for r in roles}

    for role_def in ROLES:
        payload = {
            "name": role_def.name,
            "color": role_def.color,
            "hoist": role_def.hoist,
            "mentionable": True,
        }
        if role_def.name in by_name:
            rid = by_name[role_def.name]["id"]
            pause()
            r = api("PATCH", f"/guilds/{GUILD_ID}/roles/{rid}", payload)
            print(f"  OK: {role_def.name}" if not r.get("_status") else f"  WARN: {role_def.name}")
        else:
            pause()
            r = api("POST", f"/guilds/{GUILD_ID}/roles", payload)
            print(f"  Created: {role_def.name}" if not r.get("_status") else f"  ERROR: {role_def.name}")


def main() -> int:
    if not os.environ.get("DISCORD_TOKEN"):
        print("Set DISCORD_TOKEN", file=sys.stderr)
        return 1

    print("Syncing roles...")
    sync_roles()

    channels = api("GET", f"/guilds/{GUILD_ID}/channels")
    choose = channel_by_slug(channels if isinstance(channels, list) else [], "choose-roles")
    if choose:
        pause()
        api(
            "PATCH",
            f"/channels/{choose['id']}",
            {"topic": "Pick your roles here — menus only, no chat."},
        )
        lock_choose_roles_channel(choose["id"])
        print("  Updated #choose-roles topic")

    print("\nRestart role bot for updated menus:")
    print("  DISCORD_TOKEN=... python3 scripts/discord_role_bot.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
