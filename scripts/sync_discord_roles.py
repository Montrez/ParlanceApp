#!/usr/bin/env python3
"""Delete unused Discord roles; keep only the Parlance catalog (+ staff)."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from discord_role_catalog import CURRENT_NAMES, ROLES

GUILD_ID = "1519729833079210064"
BASE = "https://discord.com/api/v10"
DELAY = 0.45

# Staff / manual roles not in the self-serve catalog
KEEP_EXTRA = frozenset({"Beta Tester", "Contributor", "Admin", "Moderator", "Member", "Bot"})


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
            "User-Agent": "ParlanceRoleSync/1.0",
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

    keep = CURRENT_NAMES | KEEP_EXTRA
    roles = api("GET", f"/guilds/{GUILD_ID}/roles")
    if not isinstance(roles, list):
        print(roles, file=sys.stderr)
        return 1

    by_name = {r["name"]: r for r in roles}
    deleted = 0
    created = 0
    updated = 0

    for role_def in ROLES:
        payload = {
            "name": role_def.name,
            "color": role_def.color,
            "hoist": role_def.hoist,
            "mentionable": True,
        }
        if role_def.name in by_name:
            rid = by_name[role_def.name]["id"]
            time.sleep(DELAY)
            r = api("PATCH", f"/guilds/{GUILD_ID}/roles/{rid}", payload)
            if not r.get("_status"):
                updated += 1
        else:
            time.sleep(DELAY)
            r = api("POST", f"/guilds/{GUILD_ID}/roles", payload)
            if not r.get("_status"):
                created += 1
                print(f"  created: {role_def.name}")

    for r in roles:
        name = r["name"]
        if name == "@everyone" or r.get("managed"):
            continue
        if name in keep:
            continue
        time.sleep(DELAY)
        out = api("DELETE", f"/guilds/{GUILD_ID}/roles/{r['id']}")
        if not out.get("_status"):
            deleted += 1
            print(f"  deleted: {name}")
        else:
            print(f"  could not delete {name}: {out}")

    print(f"\nRoles: {updated} updated, {created} created, {deleted} removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
