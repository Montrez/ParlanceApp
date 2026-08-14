#!/usr/bin/env python3
"""Post today's daily culture tip to #daily-culture (GitHub Actions cron or manual).

Skips any topic already in the channel so the 21-day wrap cannot repeat a tip.
If the same tip was posted more than once, keeps the oldest and deletes the rest.
"""
from __future__ import annotations

import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from discord_bots.config import GUILD_ID
from discord_bots.daily_culture import TOPICS, _today_et, next_unused_topic
from discord_channel_catalog import channel_by_slug, channel_name

BASE = "https://discord.com/api/v10"
SLUG = "daily-culture"
HISTORY_CAP = 500


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


def _topic_in_message(content: str) -> str | None:
    for topic in TOPICS:
        if topic["title"] in content:
            return topic["title"]
    return None


def fetch_messages(channel_id: str) -> list[dict]:
    out: list[dict] = []
    before: str | None = None
    while len(out) < HISTORY_CAP:
        path = f"/channels/{channel_id}/messages?limit=100"
        if before:
            path += f"&before={before}"
        batch = api("GET", path)
        if not isinstance(batch, list) or not batch:
            break
        out.extend(m for m in batch if isinstance(m, dict))
        before = batch[-1].get("id")
        if len(batch) < 100 or not before:
            break
        time.sleep(0.35)
    return out


def delete_repeat_posts(channel_id: str, bot_id: str, messages: list[dict]) -> int:
    """Keep the oldest post of each topic. Delete later copies from Morgan."""
    by_title: dict[str, list[dict]] = {}
    for msg in messages:
        if str(msg.get("author", {}).get("id")) != str(bot_id):
            continue
        title = _topic_in_message(msg.get("content", ""))
        if not title:
            continue
        by_title.setdefault(title, []).append(msg)

    removed = 0
    for title, copies in by_title.items():
        copies.sort(key=lambda m: str(m.get("timestamp", "")))
        for extra in copies[1:]:
            msg_id = extra.get("id")
            if not msg_id:
                continue
            result = api("DELETE", f"/channels/{channel_id}/messages/{msg_id}")
            if result.get("_status"):
                print(f"Could not delete repeat of {title}: {result}", file=sys.stderr)
                continue
            removed += 1
            print(f"Removed repeat post: {title}")
            time.sleep(0.35)
    return removed


def main() -> int:
    if not os.environ.get("DISCORD_GUIDE_TOKEN"):
        print("Set DISCORD_GUIDE_TOKEN", file=sys.stderr)
        return 1

    today = _today_et().isoformat()

    me = api("GET", "/users/@me")
    if not isinstance(me, dict) or not me.get("id"):
        print(f"Failed to identify bot user: {me}", file=sys.stderr)
        return 1
    bot_id = str(me["id"])

    channels = api("GET", f"/guilds/{GUILD_ID}/channels")
    if not isinstance(channels, list):
        print(f"Failed to list channels: {channels}", file=sys.stderr)
        return 1

    channel = channel_by_slug(channels, SLUG)
    if not channel:
        print(f"Channel {channel_name(SLUG)!r} not found", file=sys.stderr)
        return 1

    channel_id = channel["id"]
    messages = fetch_messages(channel_id)
    delete_repeat_posts(channel_id, bot_id, messages)
    messages = fetch_messages(channel_id)

    posted_titles: set[str] = set()
    posted_today = False
    for msg in messages:
        title = _topic_in_message(msg.get("content", ""))
        if not title:
            continue
        posted_titles.add(title)
        if _message_date_et(msg.get("timestamp", "")) == today:
            posted_today = True

    if posted_today:
        print("Already posted a unique tip today.")
        return 0

    topic = next_unused_topic(posted_titles)
    if not topic:
        print("All topics are already in the channel. Add more before posting again.")
        return 0

    content = f"**{topic['title']}**\n\n{topic['body']}"
    posted = api("POST", f"/channels/{channel_id}/messages", {"content": content})
    if posted.get("_status"):
        print(f"ERROR posting tip: {posted}", file=sys.stderr)
        return 1

    print(f"Posted to #{channel.get('name', SLUG)}: {topic['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
