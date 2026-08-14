#!/usr/bin/env python3
"""
Run the Parlance community bots.

Required env vars:
  DISCORD_GUIDE_TOKEN      Morgan  — FAQ replies (daily culture is GitHub Actions)
  DISCORD_SENTINEL_TOKEN   Jordan  — bugs and feedback triage

Optional:
  DISCORD_HERALD_TOKEN     Claire — owns #announcements (/announce, /release, /testflight)

  pip install -r requirements.txt
  export DISCORD_GUIDE_TOKEN=...
  export DISCORD_SENTINEL_TOKEN=...
  python3 scripts/discord_bots/run_all.py
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from discord_bots.guide import create_guide_bot
from discord_bots.sentinel import create_sentinel_bot
from discord_bots.herald import create_herald_bot

INTENT_HELP = (
    "Enable MESSAGE CONTENT INTENT in the Discord Developer Portal:\n"
    "  Bot → Privileged Gateway Intents → Message Content Intent → ON\n"
    "Jordan needs this to read posts in #bugs and #feedback."
)


async def _start(label: str, bot, token: str) -> None:
    try:
        await bot.start(token)
    except Exception as exc:
        print(f"[{label}] failed to start: {exc}", file=sys.stderr)
        if "PrivilegedIntentsRequired" in type(exc).__name__ or "privileged intents" in str(exc).lower():
            print(INTENT_HELP, file=sys.stderr)
        raise


async def main() -> None:
    guide_token = os.environ.get("DISCORD_GUIDE_TOKEN")
    sentinel_token = os.environ.get("DISCORD_SENTINEL_TOKEN")
    herald_token = os.environ.get("DISCORD_HERALD_TOKEN")

    if not guide_token and not sentinel_token and not herald_token:
        print(
            "ERROR: set DISCORD_GUIDE_TOKEN and/or DISCORD_SENTINEL_TOKEN.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    tasks: list[asyncio.Task] = []

    if guide_token:
        tasks.append(asyncio.create_task(_start("Morgan", create_guide_bot(), guide_token)))
    else:
        print("[Morgan] No DISCORD_GUIDE_TOKEN — skipping.", file=sys.stderr)

    if sentinel_token:
        tasks.append(asyncio.create_task(_start("Jordan", create_sentinel_bot(), sentinel_token)))
    else:
        print("[Jordan] No DISCORD_SENTINEL_TOKEN — skipping.", file=sys.stderr)

    if herald_token:
        tasks.append(asyncio.create_task(_start("Claire", create_herald_bot(), herald_token)))
    else:
        print("[Claire] No DISCORD_HERALD_TOKEN — skipping slash commands. Release announces still use Claire webhook.")

    if not tasks:
        raise SystemExit(1)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    failures = [r for r in results if isinstance(r, Exception)]
    if failures:
        for err in failures:
            print(f"Bot stopped: {err}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
