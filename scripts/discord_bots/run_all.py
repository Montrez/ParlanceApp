#!/usr/bin/env python3
"""
Run the three Parlance community helpers.

Create three apps in the Discord Developer Portal. Name the bots like regular members:

  Morgan   → DISCORD_GUIDE_TOKEN    (questions — #general, #support, #parlance-coach)
  Jordan   → DISCORD_SENTINEL_TOKEN (bugs & feedback)
  Parlance → DISCORD_HERALD_TOKEN   (announcements — or use your own name)

Enable Message Content Intent for Morgan and Jordan.

  pip install -r scripts/requirements-discord.txt
  export DISCORD_GUIDE_TOKEN=...
  export DISCORD_SENTINEL_TOKEN=...
  export DISCORD_HERALD_TOKEN=...
  python3 scripts/discord_bots/run_all.py
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from discord_bots.guide import create_guide_bot
from discord_bots.herald import create_herald_bot
from discord_bots.sentinel import create_sentinel_bot


async def main() -> None:
    tokens = {
        "GUIDE": os.environ.get("DISCORD_GUIDE_TOKEN"),
        "SENTINEL": os.environ.get("DISCORD_SENTINEL_TOKEN"),
        "HERALD": os.environ.get("DISCORD_HERALD_TOKEN"),
    }
    missing = [k for k, v in tokens.items() if not v]
    if missing:
        print("Missing:", ", ".join(f"DISCORD_{k}_TOKEN" for k in missing), file=sys.stderr)
        print(__doc__, file=sys.stderr)
        raise SystemExit(1)

    await asyncio.gather(
        create_guide_bot().start(tokens["GUIDE"]),
        create_sentinel_bot().start(tokens["SENTINEL"]),
        create_herald_bot().start(tokens["HERALD"]),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
