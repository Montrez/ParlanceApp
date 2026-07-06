"""Role definitions for Parlance Discord."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoleDef:
    name: str  # plain name on Discord (no emoji in role name)
    emoji: str  # icon in dropdown menus
    color: int
    hoist: bool
    group: str


GROUP_META: dict[str, tuple[str, str, int, int]] = {
    "learning": ("Learning language", "Languages you practice here", 1, 2),
    "native": ("Native language", "Your strongest or first language", 1, 1),
    "region": ("Continental region", "Where you're based (for exam centers & peers)", 1, 1),
    "path": ("Your path", "Interpreter journey stage", 1, 1),
    "exam": ("Exam interest", "Certs you're preparing for (pick any)", 0, 3),
    "interests": ("Domain focus", "Optional — medical or legal", 0, 2),
}

# group → (embed title, react hint)
GROUP_DISPLAY: dict[str, tuple[str, str]] = {
    "learning": ("🇪🇸 🇫🇷 Learning", "React with a flag — up to 2"),
    "native": ("🗣️ Native language", "React with one — replaces your previous pick"),
    "region": ("🌎 🌍 Region", "React with one globe"),
    "path": ("🎯 Your path", "React with one"),
    "exam": ("📜 🌐 Exams", "React to toggle — up to 3, or ⏳ if none yet"),
    "interests": ("🏥 ⚖️ Focus", "Optional — react to toggle"),
}

ROLE_GROUP_ORDER = ["learning", "native", "region", "path", "exam", "interests"]

ROLES: list[RoleDef] = [
    RoleDef("Spanish Learner", "🇪🇸", 0xE67E22, False, "learning"),
    RoleDef("French Learner", "🇫🇷", 0x3498DB, False, "learning"),
    RoleDef("Native: English", "🇬🇧", 0x95A5A6, False, "native"),
    RoleDef("Native: Spanish", "🇪🇸", 0xC0392B, False, "native"),
    RoleDef("Native: French", "🇫🇷", 0x2980B9, False, "native"),
    RoleDef("Native: Portuguese", "🇵🇹", 0x27AE60, False, "native"),
    RoleDef("Native: German", "🇩🇪", 0xF1C40F, False, "native"),
    RoleDef("Native: Italian", "🇮🇹", 0x2ECC71, False, "native"),
    RoleDef("Native: Mandarin", "🇨🇳", 0xE74C3C, False, "native"),
    RoleDef("Native: Arabic", "🇸🇦", 0x1ABC9C, False, "native"),
    RoleDef("Native: Japanese", "🇯🇵", 0xE91E63, False, "native"),
    RoleDef("Native: Korean", "🇰🇷", 0x3498DB, False, "native"),
    RoleDef("Native: Russian", "🇷🇺", 0x5D6D7E, False, "native"),
    RoleDef("Native: Other", "🌍", 0x7F8C8D, False, "native"),
    RoleDef("North America", "🌎", 0x5865F2, False, "region"),
    RoleDef("Latin America", "🌴", 0xE67E22, False, "region"),
    RoleDef("Europe", "🌍", 0x3498DB, False, "region"),
    RoleDef("Asia-Pacific", "🌏", 0x9B59B6, False, "region"),
    RoleDef("Africa", "🌐", 0xF39C12, False, "region"),
    RoleDef("Middle East", "🧭", 0x1ABC9C, False, "region"),
    RoleDef("Oceania", "🏝️", 0x1DA1F2, False, "region"),
    RoleDef("Aspiring Interpreter", "🎯", 0x9B59B6, True, "path"),
    RoleDef("Working Interpreter", "🎧", 0x8E44AD, True, "path"),
    RoleDef("Language Student", "📚", 0xF39C12, False, "path"),
    RoleDef("DELE", "📜", 0xE74C3C, False, "exam"),
    RoleDef("SIELE", "🌐", 0xE67E22, False, "exam"),
    RoleDef("DELF", "📋", 0x3498DB, False, "exam"),
    RoleDef("DALF", "📚", 0x2980B9, False, "exam"),
    RoleDef("TCF", "🗣️", 0x5DADE2, False, "exam"),
    RoleDef("No Exam Yet", "⏳", 0xBDC3C7, False, "exam"),
    RoleDef("Medical Domain", "🏥", 0x27AE60, False, "interests"),
    RoleDef("Legal Domain", "⚖️", 0x2C3E50, False, "interests"),
]

ROLE_GROUPS: dict[str, list[str]] = {}
for _r in ROLES:
    ROLE_GROUPS.setdefault(_r.group, []).append(_r.name)

ROLE_EMOJI: dict[str, str] = {r.name: r.emoji for r in ROLES}

CURRENT_NAMES = {r.name for r in ROLES}
