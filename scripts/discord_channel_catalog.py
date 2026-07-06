"""Canonical Discord channel slugs and display names (emoji prefixes)."""
from __future__ import annotations

import re

# Internal slug → live Discord channel name
CHANNEL_NAMES: dict[str, str] = {
    "whats-new": "🆕-whats-new",
    "choose-roles": "🎭-choose-roles",
    "rules": "📜-rules",
    "announcements": "📢-announcements",
    "general": "💬-general",
    "introductions": "👋-introductions",
    "support": "🆘-support",
    "feedback": "💡-feedback",
    "bugs": "🐛-bugs",
    "beta-testers": "🧪-beta-testers",
    "parlance-coach": "🎓-parlance-coach",
    "spanish-practice": "🇪🇸-spanish-practice",
    "french-practice": "🇫🇷-french-practice",
    "find-a-seat": "📍-find-a-seat",
    "dele": "📝-dele",
    "siele": "💻-siele",
    "delf": "📋-delf",
    "dalf": "📚-dalf",
    "tcf": "🗣️-tcf",
    "passed": "🎉-passed",
}

# Category slug (uppercase key) → live Discord category name
CATEGORY_NAMES: dict[str, str] = {
    "WELCOME": "✨ WELCOME",
    "COMMUNITY": "🌍 COMMUNITY",
    "PRODUCT": "📱 PRODUCT",
    "SPANISH": "🇪🇸 ESPAÑOL",
    "FRENCH": "🇫🇷 FRANÇAIS",
    "EXAMS": "🎯 EXAMS",
}

EXAM_CATEGORY = CATEGORY_NAMES["EXAMS"]

_SLUG_BY_ANY_NAME: dict[str, str] = {}
for slug, display in CHANNEL_NAMES.items():
    _SLUG_BY_ANY_NAME[slug] = slug
    _SLUG_BY_ANY_NAME[display] = slug


def slug_from_name(name: str) -> str | None:
    if name in _SLUG_BY_ANY_NAME:
        return _SLUG_BY_ANY_NAME[name]
    m = re.match(r"^.+?-(?P<tail>.+)$", name)
    if m and m.group("tail") in CHANNEL_NAMES:
        return m.group("tail")
    return None


def channel_name(slug: str) -> str:
    return CHANNEL_NAMES.get(slug, slug)


def category_name(slug: str) -> str:
    return CATEGORY_NAMES.get(slug, slug)


def channel_mention(slug: str) -> str:
    return f"#{channel_name(slug)}"


def matches_slug(channel_name_value: str, slug: str) -> bool:
    return channel_name_value in (channel_name(slug), slug)


def channel_by_slug(channels: list[dict], slug: str) -> dict | None:
    names = {channel_name(slug), slug}
    for ch in channels:
        if ch.get("name") in names:
            return ch
    return None


def get_text_channel(guild, slug: str):
    import discord

    ch = discord.utils.get(guild.text_channels, name=channel_name(slug))
    if ch:
        return ch
    return discord.utils.get(guild.text_channels, name=slug)
