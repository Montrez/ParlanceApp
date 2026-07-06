"""Jordan — bugs and feedback, calm and practical."""
from __future__ import annotations

import re

import discord
from discord.ext import commands

from .config import CHANNELS, GUILD_ID
from .personalities import BUG_TEMPLATE, FEEDBACK_TEMPLATE, SENTINEL

BUG_HINTS = re.compile(
    r"(device|iphone|ipad|ios|android|version|build|steps|reproduce|expected|screenshot)",
    re.I,
)
FEEDBACK_HINTS = re.compile(r"(want|because|why|priority|suggest|feature|idea)", re.I)


class SentinelBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self._seen: set[int] = set()

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    def _channel_kind(self, channel: discord.TextChannel) -> str | None:
        if channel.name == CHANNELS["bugs"]:
            return "bug"
        if channel.name == CHANNELS["feedback"]:
            return "feedback"
        return None

    def _needs_nudge(self, kind: str, text: str) -> bool:
        if len(text.strip()) < 40:
            return True
        hints = BUG_HINTS if kind == "bug" else FEEDBACK_HINTS
        return len(hints.findall(text)) < 2

    async def on_ready(self):
        print(f"[{SENTINEL['name']}] online as {self.user}")

    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if not isinstance(message.channel, discord.TextChannel):
            return
        kind = self._channel_kind(message.channel)
        if not kind:
            return
        if message.id in self._seen:
            return
        self._seen.add(message.id)
        if len(self._seen) > 500:
            self._seen.clear()

        if not self._needs_nudge(kind, message.content):
            await message.add_reaction("✅")
            await message.reply("Thanks — noted.", mention_author=False)
            return

        template = BUG_TEMPLATE if kind == "bug" else FEEDBACK_TEMPLATE
        opener = (
            "This'll help us track it down:"
            if kind == "bug"
            else "A bit more context would help:"
        )
        thread_name = f"{message.author.display_name}"[:100]
        thread = await message.create_thread(name=thread_name, auto_archive_duration=10080)
        await thread.send(f"{message.author.mention} {opener}\n\n{template}")

    @commands.hybrid_command(name="template", description="Bug or feedback template")
    async def template_cmd(self, ctx: commands.Context, kind: str = "bug"):
        body = BUG_TEMPLATE if kind.lower().startswith("bug") else FEEDBACK_TEMPLATE
        await ctx.reply(body, mention_author=False)


def create_sentinel_bot() -> SentinelBot:
    return SentinelBot()
