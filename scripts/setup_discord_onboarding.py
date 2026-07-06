#!/usr/bin/env python3
"""
One-shot setup for Parlance Discord onboarding.

- Creates Admin, Moderator, Bot, and Member roles
- Syncs / cleans up all catalog roles
- Gates channels: @everyone can only see WELCOME + #choose-roles until they pick a role
- Assigns Admin to the server owner and Bot role to the Parlance bot
- Posts an onboarding announcement in #announcements
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
from discord_role_catalog import CURRENT_NAMES, ROLES

GUILD_ID   = "1519729833079210064"
OWNER_ID   = "355102156241764352"   # cmontrez (server owner)
BASE       = "https://discord.com/api/v10"
DELAY      = 0.55

# Channels everyone can see before picking roles
PUBLIC_SLUGS = {"choose-roles", "rules", "announcements"}

STAFF_ROLES = [
    {"name": "Admin",     "color": 0xE74C3C, "hoist": True,  "permissions": "8"},   # Administrator
    {"name": "Moderator", "color": 0xE67E22, "hoist": True,  "permissions": "1099511627775"},  # Manage messages + kick/ban
    {"name": "Bot",       "color": 0x7289DA, "hoist": False, "permissions": "8"},   # Administrator
    {"name": "Member",    "color": 0x2ECC71, "hoist": False, "permissions": "0"},   # No extra perms — used for gating
]

KEEP_ALWAYS = CURRENT_NAMES | {r["name"] for r in STAFF_ROLES} | {"Beta Tester", "Contributor"}


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
            "User-Agent": "ParlanceOnboarding/1.0",
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


# ── helpers ──────────────────────────────────────────────────────────────────

def get_or_create_role(by_name: dict, name: str, **kwargs) -> str:
    if name in by_name:
        rid = by_name[name]["id"]
        pause()
        api("PATCH", f"/guilds/{GUILD_ID}/roles/{rid}", {"name": name, **kwargs})
        print(f"  updated role: {name}")
        return rid
    pause()
    r = api("POST", f"/guilds/{GUILD_ID}/roles", {"name": name, **kwargs})
    if r.get("_status"):
        raise RuntimeError(f"Could not create role '{name}': {r}")
    print(f"  created role: {name}")
    return r["id"]


def assign_role(user_id: str, role_id: str, label: str) -> None:
    pause()
    r = api("PUT", f"/guilds/{GUILD_ID}/members/{user_id}/roles/{role_id}")
    if isinstance(r, dict) and r.get("_status") and r["_status"] != 204:
        print(f"  WARN: could not assign {label} to {user_id}: {r}")
    else:
        print(f"  assigned {label} → {user_id}")


def get_bot_user_id() -> str:
    r = api("GET", "/users/@me")
    if isinstance(r, dict) and "id" in r:
        return r["id"]
    raise RuntimeError(f"Could not fetch bot user: {r}")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    if not os.environ.get("DISCORD_TOKEN"):
        print("Set DISCORD_TOKEN", file=sys.stderr)
        return 1

    bot_id = get_bot_user_id()
    print(f"Bot ID: {bot_id}\n")

    # ── 1. Fetch current roles ────────────────────────────────────────────────
    roles = api("GET", f"/guilds/{GUILD_ID}/roles")
    if not isinstance(roles, list):
        print(f"Error fetching roles: {roles}", file=sys.stderr)
        return 1
    by_name = {r["name"]: r for r in roles}

    # ── 2. Create / update staff roles ───────────────────────────────────────
    print("── Staff roles ──────────────────────────────────────")
    staff_ids: dict[str, str] = {}
    for sr in STAFF_ROLES:
        rid = get_or_create_role(
            by_name, sr["name"],
            color=sr["color"],
            hoist=sr["hoist"],
            permissions=sr["permissions"],
            mentionable=False,
        )
        staff_ids[sr["name"]] = rid

    # ── 3. Sync catalog roles ─────────────────────────────────────────────────
    print("\n── Catalog roles ────────────────────────────────────")
    pause()
    roles = api("GET", f"/guilds/{GUILD_ID}/roles")   # refresh
    by_name = {r["name"]: r for r in roles}

    for role_def in ROLES:
        payload = {"name": role_def.name, "color": role_def.color,
                   "hoist": role_def.hoist, "mentionable": True}
        if role_def.name in by_name:
            rid = by_name[role_def.name]["id"]
            pause()
            api("PATCH", f"/guilds/{GUILD_ID}/roles/{rid}", payload)
        else:
            pause()
            r = api("POST", f"/guilds/{GUILD_ID}/roles", payload)
            if not r.get("_status"):
                print(f"  created: {role_def.name}")

    # ── 4. Delete stale roles ─────────────────────────────────────────────────
    print("\n── Cleanup ──────────────────────────────────────────")
    pause()
    roles = api("GET", f"/guilds/{GUILD_ID}/roles")
    deleted = 0
    for r in roles:
        if r["name"] == "@everyone" or r.get("managed"):
            continue
        if r["name"] in KEEP_ALWAYS:
            continue
        pause()
        out = api("DELETE", f"/guilds/{GUILD_ID}/roles/{r['id']}")
        if not (isinstance(out, dict) and out.get("_status")):
            deleted += 1
            print(f"  deleted: {r['name']}")
        else:
            print(f"  could not delete {r['name']}: {out}")
    print(f"  {deleted} stale role(s) removed")

    # ── 5. Assign Admin to owner, Bot role to bot ─────────────────────────────
    print("\n── Role assignments ─────────────────────────────────")
    assign_role(OWNER_ID, staff_ids["Admin"], "Admin")
    assign_role(bot_id,   staff_ids["Bot"],   "Bot")

    # ── 6. Gate channels ──────────────────────────────────────────────────────
    print("\n── Channel permissions ──────────────────────────────")
    pause()
    channels = api("GET", f"/guilds/{GUILD_ID}/channels")
    if not isinstance(channels, list):
        print(f"Error fetching channels: {channels}", file=sys.stderr)
        return 1

    # Get @everyone and Member role IDs
    pause()
    roles = api("GET", f"/guilds/{GUILD_ID}/roles")
    role_ids: dict[str, str] = {r["name"]: r["id"] for r in roles}
    everyone_id  = role_ids.get("@everyone", GUILD_ID)
    member_rid   = staff_ids.get("Member", role_ids.get("Member", ""))

    # VIEW_CHANNEL = 0x400 (1024), SEND_MESSAGES = 0x800 (2048)
    VIEW = 1024

    for ch in channels:
        if ch.get("type") != 0:   # text channels only
            continue
        slug = slug_from_name(ch.get("name", ""))
        cid  = ch["id"]

        if slug in PUBLIC_SLUGS:
            # Explicitly allow @everyone to view
            pause()
            api("PUT", f"/channels/{cid}/permissions/{everyone_id}", {
                "allow": str(VIEW), "deny": "0", "type": 0
            })
            print(f"  public: #{channel_name(slug) if slug else ch['name']}")
        else:
            # Deny @everyone, allow Member+
            pause()
            api("PUT", f"/channels/{cid}/permissions/{everyone_id}", {
                "allow": "0", "deny": str(VIEW), "type": 0
            })
            if member_rid:
                pause()
                api("PUT", f"/channels/{cid}/permissions/{member_rid}", {
                    "allow": str(VIEW), "deny": "0", "type": 0
                })
            print(f"  gated:  #{channel_name(slug) if slug else ch['name']}")

    # ── 7. Post announcement ──────────────────────────────────────────────────
    print("\n── Announcement ─────────────────────────────────────")
    ann_id = None
    for ch in channels:
        slug = slug_from_name(ch.get("name", ""))
        if slug == "announcements":
            ann_id = ch["id"]
            break

    if ann_id:
        choose_ch = channel_name("choose-roles")
        rules_ch  = channel_name("rules")
        msg = (
            "👋 **Welcome to Parlance!**\n\n"
            "Before you can explore the server, complete these two steps:\n\n"
            f"**1.** Read the server guidelines in #{rules_ch}\n"
            f"**2.** Head to #{choose_ch} and react with your emojis to set your roles\n"
            "      — your learning language, region, path, and exam goals\n\n"
            "Once you've picked at least one role, all channels will unlock automatically. "
            "It takes about 30 seconds. 🎉"
        )
        # Delete any previous onboarding announcement from the bot
        bot_msgs = api("GET", f"/channels/{ann_id}/messages?limit=20")
        if isinstance(bot_msgs, list):
            for m in bot_msgs:
                if m.get("author", {}).get("id") == bot_id and "Welcome to Parlance" in (m.get("content") or ""):
                    pause()
                    api("DELETE", f"/channels/{ann_id}/messages/{m['id']}")

        pause()
        r = api("POST", f"/channels/{ann_id}/messages", {"content": msg})
        if "id" in r:
            print(f"  posted announcement in #announcements")
        else:
            print(f"  ERROR posting announcement: {r}")
    else:
        print("  #announcements not found — skipping")

    print("\n✅ Onboarding setup complete.")
    print("   Restart the role bot so it can auto-assign Member when someone picks their first role:")
    print("   python3 scripts/discord_role_bot.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
