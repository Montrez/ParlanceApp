#!/usr/bin/env python3
"""Parlance Discord — emoji reaction roles + find-a-seat (no buttons, no Firebase)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import discord
except ImportError:
    print("Install: pip install discord.py", file=sys.stderr)
    raise SystemExit(1)

from discord_channel_catalog import channel_mention, get_text_channel
from discord_role_catalog import GROUP_META, ROLE_EMOJI, ROLE_GROUP_ORDER, ROLE_GROUPS

GUILD_ID = 1519729833079210064
CHOOSE_ROLES_SLUG = "choose-roles"
REACT_MARKER = "parlance-react"

# emoji → role name
EMOJI_TO_ROLE = {v: k for k, v in ROLE_EMOJI.items()}


def group_from_message(content: str) -> str | None:
    for group in ROLE_GROUP_ORDER:
        if f"{REACT_MARKER}-{group}" in content:
            return group
    return None


class ParlanceRoleBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.guild_reactions = True
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f"Reaction roles live as {self.user}")
        print(f"Listening in {channel_mention('choose-roles')}")

    async def _role_ids_for_group(self, guild: discord.Guild, group: str) -> set[int]:
        ids: set[int] = set()
        for name in ROLE_GROUPS.get(group, []):
            role = discord.utils.get(guild.roles, name=name)
            if role:
                ids.add(role.id)
        return ids

    async def _emoji_for_role(self, guild: discord.Guild, role_id: int) -> str | None:
        role = guild.get_role(role_id)
        if not role:
            return None
        return ROLE_EMOJI.get(role.name)

    async def _clear_other_reactions(
        self,
        channel_id: int,
        message_id: int,
        user_id: int,
        keep_emoji: str,
    ) -> None:
        channel = self.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        try:
            msg = await channel.fetch_message(message_id)
        except discord.HTTPException:
            return
        for react in msg.reactions:
            if str(react.emoji) == keep_emoji:
                continue
            async for user in react.users():
                if user.id == user_id:
                    try:
                        await msg.remove_reaction(react.emoji, user)
                    except discord.HTTPException:
                        pass

    async def _apply(
        self,
        guild: discord.Guild,
        member: discord.Member,
        group: str,
        role_name: str,
        *,
        adding: bool,
    ) -> str:
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            return "Role missing on server — ask an admin to run sync_discord_roles.py"

        gids = await self._role_ids_for_group(guild, group)
        current = [r for r in member.roles if r.id in gids]
        _, _, _min_v, max_v = GROUP_META[group]

        if not adding:
            if max_v == 1:
                return ""
            if role in current:
                await member.remove_roles(role, reason="Reaction role removed")
                return f"**{role_name}** removed"
            return ""

        if max_v == 1:
            if role in current:
                return ""
            for r in current:
                await member.remove_roles(r, reason="Reaction role swap")
            await member.add_roles(role, reason="Reaction role")
            if current:
                return f"**{role_name}** (replaced {current[0].name})"
            return f"**{role_name}** added"

        if role in current:
            return ""

        to_remove: list[discord.Role] = []
        if group == "exam" and role_name == "No Exam Yet":
            to_remove = list(current)
        elif group == "exam":
            to_remove = [r for r in current if r.name == "No Exam Yet"]
            active = [r for r in current if r.name != "No Exam Yet"]
            if len(active) >= max_v:
                to_remove.append(active[0])
        elif len(current) >= max_v:
            to_remove = [current[0]]

        for r in to_remove:
            await member.remove_roles(r, reason="Reaction role")
        await member.add_roles(role, reason="Reaction role")
        if to_remove:
            return f"**{role_name}** (replaced {', '.join(r.name for r in to_remove)})"
        return f"**{role_name}** added"

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.user.id:
            return
        guild = self.get_guild(payload.guild_id)
        if not guild or payload.guild_id != GUILD_ID:
            return
        channel = guild.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        choose = get_text_channel(guild, CHOOSE_ROLES_SLUG)
        if not choose or channel.id != choose.id:
            return

        try:
            msg = await channel.fetch_message(payload.message_id)
        except discord.HTTPException:
            return
        group = group_from_message(msg.content or "")
        if not group:
            return

        emoji = str(payload.emoji)
        role_name = EMOJI_TO_ROLE.get(emoji)
        if not role_name or role_name not in ROLE_GROUPS.get(group, []):
            return

        member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        _, _, _min_v, max_v = GROUP_META[group]
        if max_v == 1:
            await self._clear_other_reactions(channel.id, msg.id, member.id, emoji)

        note = await self._apply(guild, member, group, role_name, adding=True)

        # Auto-assign Member role on first role pick (unlocks gated channels)
        member_role = discord.utils.get(guild.roles, name="Member")
        if member_role and member_role not in member.roles:
            try:
                await member.add_roles(member_role, reason="First role selected — unlocking channels")
            except discord.HTTPException:
                pass

        if note:
            try:
                await member.send(f"{note}\n\nAll channels are now unlocked — welcome to Parlance! 🎉")
            except discord.HTTPException:
                pass

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.user.id:
            return
        guild = self.get_guild(payload.guild_id)
        if not guild or payload.guild_id != GUILD_ID:
            return
        channel = guild.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        choose = get_text_channel(guild, CHOOSE_ROLES_SLUG)
        if not choose or channel.id != choose.id:
            return

        try:
            msg = await channel.fetch_message(payload.message_id)
        except discord.HTTPException:
            return
        group = group_from_message(msg.content or "")
        if not group:
            return

        emoji = str(payload.emoji)
        role_name = EMOJI_TO_ROLE.get(emoji)
        if not role_name:
            return

        member = guild.get_member(payload.user_id)
        if not member:
            return
        note = await self._apply(guild, member, group, role_name, adding=False)
        if note:
            try:
                await member.send(note)
            except discord.HTTPException:
                pass


def main() -> int:
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("Set DISCORD_TOKEN", file=sys.stderr)
        return 1
    ParlanceRoleBot().run(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
