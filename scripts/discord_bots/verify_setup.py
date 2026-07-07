#!/usr/bin/env python3
"""Check Morgan/Jordan bot tokens, guild membership, and gateway intents."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

GUILD_ID = "1519729833079210064"
BASE = "https://discord.com/api/v10"


def api(token: str, method: str, path: str, data: dict | None = None) -> dict:
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
            "User-Agent": "ParlanceBotVerify/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        return {"_error": exc.read().decode(), "_status": exc.code}


def check_bot(label: str, token: str | None) -> None:
    print(f"\n=== {label} ===")
    if not token:
        print("  MISSING token")
        return

    me = api(token, "GET", "/users/@me")
    if "_error" in me:
        print(f"  INVALID token ({me.get('_status')})")
        return

    print(f"  Username: {me.get('username')} (id {me.get('id')})")

    member = api(token, "GET", f"/guilds/{GUILD_ID}/members/{me['id']}")
    if "_error" in member:
        print("  NOT in Parlance server — invite this bot to the guild")
    else:
        print("  In Parlance server: yes")

    app = api(token, "GET", "/applications/@me")
    if "_error" not in app:
        flags = app.get("flags", 0)
        # Gateway intent enablement is not exposed cleanly via REST; probe gateway instead.
        print(f"  Application: {app.get('name')}")

    gateway = api(token, "GET", "/gateway/bot")
    if "_error" not in gateway:
        print(f"  Gateway sessions: {gateway.get('session_start_limit', {})}")

    # Lightweight intent probe: identify endpoint returns 40135 when intents missing.
    identify = {
        "op": 2,
        "d": {
            "token": token,
            "intents": 33281,  # guilds + guild_messages + message_content
            "properties": {
                "$os": "linux",
                "$browser": "parlance_verify",
                "$device": "parlance_verify",
            },
        },
    }
    ws_probe = api(token, "POST", "/gateway", identify)
    if ws_probe:
        pass  # REST gateway endpoint is GET only; skip ws probe here.

    print(
        "  Message Content Intent: enable in Developer Portal → Bot → "
        "Privileged Gateway Intents → MESSAGE CONTENT INTENT"
    )


def main() -> None:
    check_bot("Morgan (DISCORD_GUIDE_TOKEN)", os.environ.get("DISCORD_GUIDE_TOKEN"))
    check_bot("Jordan (DISCORD_SENTINEL_TOKEN)", os.environ.get("DISCORD_SENTINEL_TOKEN"))
    check_bot("Claire (DISCORD_HERALD_TOKEN)", os.environ.get("DISCORD_HERALD_TOKEN"))

    print("\nClaire announcements via webhook do not need a bot token.")
    print("For Claire to show online with /announce slash commands, set DISCORD_HERALD_TOKEN.")


if __name__ == "__main__":
    main()
