#!/usr/bin/env python3
"""Post today's daily culture tip to #daily-culture (manual test or cron)."""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from discord_bots.config import CHANNELS, GUILD_ID
from discord_bots.daily_culture import TOPICS, _topic_for_today


async def main() -> None:
    import discord

    token = os.environ.get("DISCORD_GUIDE_TOKEN")
    if not token:
        print("Set DISCORD_GUIDE_TOKEN", file=sys.stderr)
        raise SystemExit(1)

    topic = _topic_for_today()
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        guild = client.get_guild(GUILD_ID)
        if not guild:
            print(f"Guild {GUILD_ID} not found", file=sys.stderr)
            await client.close()
            return
        channel = discord.utils.get(guild.text_channels, name=CHANNELS["daily_culture"])
        if not channel:
            print(f"Channel {CHANNELS['daily_culture']!r} not found", file=sys.stderr)
            await client.close()
            return
        await channel.send(f"**{topic['title']}**\n\n{topic['body']}")
        print(f"Posted to #{channel.name}: {topic['title']}")
        await client.close()

    await client.start(token)


if __name__ == "__main__":
    asyncio.run(main())
