#!/usr/bin/env python3
"""
Post emoji reaction role messages in #choose-roles.

React with an emoji to get a role. The Parlance bot adds the reactions and
handles add/remove (run: python3 scripts/discord_role_bot.py).

No Firebase, no paid hosting, no dropdown buttons.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from discord_channel_catalog import channel_by_slug, channel_mention
from discord_role_catalog import GROUP_DISPLAY, ROLE_EMOJI, ROLE_GROUP_ORDER, ROLE_GROUPS

GUILD_ID = "1519729833079210064"
BASE = "https://discord.com/api/v10"
DELAY = 0.5
MARKER = "parlance-react"
INTRO_MARKER = "parlance-react-intro"


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
            "User-Agent": "ParlanceReactionRoles/1.0",
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


def add_reaction(channel_id: str, message_id: str, emoji: str) -> None:
    encoded = urllib.parse.quote(emoji)
    api("PUT", f"/channels/{channel_id}/messages/{message_id}/reactions/{encoded}/@me")


def group_message(group: str) -> str:
    title, hint = GROUP_DISPLAY[group]
    lines = [f"**{title}**", hint, ""]
    for name in ROLE_GROUPS[group]:
        lines.append(f"{ROLE_EMOJI[name]} — **{name}**")
    return "\n".join(lines)


def main() -> int:
    if not os.environ.get("DISCORD_TOKEN"):
        print("Set DISCORD_TOKEN", file=sys.stderr)
        return 1

    channels = api("GET", f"/guilds/{GUILD_ID}/channels")
    choose = channel_by_slug(channels if isinstance(channels, list) else [], "choose-roles")
    if not choose:
        print("choose-roles not found", file=sys.stderr)
        return 1

    cid = choose["id"]
    msgs = api("GET", f"/channels/{cid}/messages?limit=50")
    if isinstance(msgs, list):
        for msg in msgs:
            content = msg.get("content") or ""
            if msg.get("components") or "parlance-role" in content or "parlance-react" in content:
                api("DELETE", f"/channels/{cid}/messages/{msg['id']}")
                time.sleep(0.35)

    intro = (
        "**Pick your roles** — react with the emoji below each section.\n\n"
        "React again to remove a role. Picking a new emoji in a **single-choice** section "
        "replaces your old role automatically.\n\n"
        f"Exam prep: **EXAMS** · {channel_mention('find-a-seat')}"
    )
    time.sleep(DELAY)
    intro_msg = api("POST", f"/channels/{cid}/messages", {"content": f"{INTRO_MARKER}\n{intro}"})
    print("Posted intro")

    for group in ROLE_GROUP_ORDER:
        time.sleep(DELAY)
        text = f"{MARKER}-{group}\n{group_message(group)}"
        posted = api("POST", f"/channels/{cid}/messages", {"content": text})
        if posted.get("_status") or "id" not in posted:
            print(f"  failed #{group}: {posted}")
            continue
        mid = posted["id"]
        for name in ROLE_GROUPS[group]:
            time.sleep(0.35)
            add_reaction(cid, mid, ROLE_EMOJI[name])
        print(f"  posted reactions: {group}")

    print("\nReactions are posted. Start the handler when you want roles to apply:")
    print("  python3 scripts/discord_role_bot.py")
    print("(Enable Server Members Intent in the Discord Developer Portal if the bot asks.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
