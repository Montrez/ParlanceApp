#!/usr/bin/env python3
"""Post today's daily culture tip to #daily-culture (GitHub Actions cron or manual)."""
from __future__ import annotations

import datetime
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from discord_bots.config import GUILD_ID
from discord_bots.daily_culture import _today_et, _topic_for_today
from discord_channel_catalog import channel_by_slug, channel_name

BASE = "https://discord.com/api/v10"
SLUG = "daily-culture"


def _message_date_et(timestamp: str) -> str:
    if not timestamp:
        return ""
    try:
        from zoneinfo import ZoneInfo

        dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.astimezone(ZoneInfo("America/New_York")).date().isoformat()
    except Exception:
        return timestamp[:10]


def api(method: str, path: str, data: dict | None = None) -> dict | list:
    token = os.environ["DISCORD_GUIDE_TOKEN"]
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
            "User-Agent": "ParlanceDailyCulture/1.0",
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


def main() -> int:
    if not os.environ.get("DISCORD_GUIDE_TOKEN"):
        print("Set DISCORD_GUIDE_TOKEN", file=sys.stderr)
        return 1

    topic = _topic_for_today()
    content = f"**{topic['title']}**\n\n{topic['body']}"
    today = _today_et().isoformat()

    channels = api("GET", f"/guilds/{GUILD_ID}/channels")
    if not isinstance(channels, list):
        print(f"Failed to list channels: {channels}", file=sys.stderr)
        return 1

    channel = channel_by_slug(channels, SLUG)
    if not channel:
        print(f"Channel {channel_name(SLUG)!r} not found", file=sys.stderr)
        return 1

    channel_id = channel["id"]
    msgs = api("GET", f"/channels/{channel_id}/messages?limit=20")
    if isinstance(msgs, list):
        needle = topic["title"]
        for msg in msgs:
            if not isinstance(msg, dict):
                continue
            if needle not in msg.get("content", ""):
                continue
            if _message_date_et(msg.get("timestamp", "")) == today:
                print(f"Already posted today: {topic['title']}")
                return 0

    posted = api("POST", f"/channels/{channel_id}/messages", {"content": content})
    if posted.get("_status"):
        print(f"ERROR posting tip: {posted}", file=sys.stderr)
        return 1

    print(f"Posted to #{channel.get('name', SLUG)}: {topic['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
