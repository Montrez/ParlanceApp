"""Shared Parlance Discord bot configuration."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from discord_channel_catalog import CHANNEL_NAMES

GUILD_ID = 1519729833079210064

# Channel slugs → live Discord names (emoji prefixes)
CHANNELS = {
    "general": CHANNEL_NAMES["general"],
    "daily_culture": CHANNEL_NAMES["daily-culture"],
    "support": CHANNEL_NAMES["support"],
    "coach": CHANNEL_NAMES["parlance-coach"],
    "bugs": CHANNEL_NAMES["bugs"],
    "feedback": CHANNEL_NAMES["feedback"],
    "announcements": CHANNEL_NAMES["announcements"],
    "whats-new": CHANNEL_NAMES["whats-new"],
}

# Roles that can use Herald slash commands (plus server admins)
HERALD_ADMIN_ROLE_NAMES = frozenset({"Contributor", "Beta Tester"})


def admin_member(member) -> bool:
    if member.guild_permissions.manage_guild or member.guild_permissions.administrator:
        return True
    if member.id == member.guild.owner_id:
        return True
    return any(r.name in ("Contributor", "Beta Tester") for r in member.roles)
