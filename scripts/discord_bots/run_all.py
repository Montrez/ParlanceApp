#!/usr/bin/env python3
"""
Run the Parlance community bots.

Required env vars:
  DISCORD_GUIDE_TOKEN      Morgan  — FAQ and daily culture posts
  DISCORD_SENTINEL_TOKEN   Jordan  — bugs and feedback triage

Optional:
  DISCORD_HERALD_TOKEN     Parlance Herald — slash commands for announcements
                           (leave unset if using webhooks instead)

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


async def main() -> None:
    guide_token    = os.environ.get("DISCORD_GUIDE_TOKEN")
    sentinel_token = os.environ.get("DISCORD_SENTINEL_TOKEN")
    herald_token   = os.environ.get("DISCORD_HERALD_TOKEN")

    if not guide_token or not sentinel_token:
        print("ERROR: DISCORD_GUIDE_TOKEN and DISCORD_SENTINEL_TOKEN are required.", file=sys.stderr)
        raise SystemExit(1)

    bots = [
        create_guide_bot().start(guide_token),
        create_sentinel_bot().start(sentinel_token),
    ]
    if herald_token:
        bots.append(create_herald_bot().start(herald_token))
    else:
        print("[Herald] No DISCORD_HERALD_TOKEN set — skipping (webhooks handle announcements).")

    await asyncio.gather(*bots)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
