"""Morgan — general Parlance questions, warm and direct."""
from __future__ import annotations

import os
import sys

import discord
from discord.ext import commands

from .config import CHANNELS, GUILD_ID
from .personalities import GUIDE, GUIDE_FAQ
from .daily_culture import DailyCultureCog

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from discord_channel_catalog import channel_mention  # noqa: E402


def _faq_answer(text: str) -> str | None:
    lower = text.lower()
    for keys, answer in GUIDE_FAQ:
        if any(k in lower for k in keys):
            return answer
    return None


def _default_reply() -> str:
    return (
        "Happy to help — a few things people ask about often:\n"
        "• Parlance Coach (on-device, no key)\n"
        "• Cloud AI and sign-in\n"
        "• Spanish and French practice\n"
        "• TestFlight builds\n"
        f"• Roles in {channel_mention('choose-roles')}\n\n"
        "What's on your mind?"
    )


class GuideBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.message_content = True
        super().__init__(command_prefix="?", intents=intents)

    async def setup_hook(self):
        await self.add_cog(DailyCultureCog(self))
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    def _allowed(self, channel: discord.abc.GuildChannel | None) -> bool:
        if not isinstance(channel, discord.TextChannel):
            return False
        return channel.name in (
            CHANNELS["general"],
            CHANNELS["support"],
            CHANNELS["coach"],
        )

    async def on_ready(self):
        print(f"[{GUIDE['name']}] online as {self.user}")

    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if not self._allowed(message.channel):
            return

        mentioned = self.user and self.user.id in [u.id for u in message.mentions]
        lower = message.content.lower().strip()
        prefixed = lower.startswith(("?help", "?parlance"))
        if not mentioned and not prefixed:
            return

        text = message.content
        for m in message.mentions:
            text = text.replace(f"<@{m.id}>", "").replace(f"<@!{m.id}>", "")
        for prefix in ("?help", "?parlance", "?"):
            if text.lower().startswith(prefix):
                text = text[len(prefix) :].strip()
                break

        body = _faq_answer(text) if text else _default_reply()
        await message.reply(body, mention_author=False)

    @commands.hybrid_command(name="help", description="Ask a question about Parlance")
    async def help_cmd(self, ctx: commands.Context, *, question: str = ""):
        body = _faq_answer(question) if question else _default_reply()
        await ctx.reply(body, mention_author=False)


def create_guide_bot() -> GuideBot:
    return GuideBot()
