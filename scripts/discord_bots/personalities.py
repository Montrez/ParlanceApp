"""
Three community helpers — set these usernames in the Discord Developer Portal (Bot → Username).

  Morgan  — general questions (#general, #support, #parlance-coach)
  Jordan  — bugs & feedback (#bugs, #feedback)
  Claire   — announcements (#announcements) — optional if using webhooks

Each has a different voice. Replies are plain text, not branded embeds.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from discord_channel_catalog import channel_mention

GUIDE = {
    "name": "Morgan",
    "color": 0x95A5A6,
}

SENTINEL = {
    "name": "Jordan",
    "color": 0x95A5A6,
}

HERALD = {
    "name": "Claire",
    "color": 0x95A5A6,
}

GUIDE_FAQ = [
    (
        ("coach", "parlance coach", "on-device", "offline"),
        "Coach runs on your device for Spanish and French — no API key. "
        "Open the journal, tap ⚙ AI, and pick Parlance Coach.",
    ),
    (
        ("api", "groq", "key", "cloud", "sign in", "firebase"),
        "Cloud AI needs Apple or Google sign-in, or your own key (Groq is free). "
        "You get about 30 cloud calls a month; Coach on-device is unlimited.",
    ),
    (
        ("testflight", "beta", "ios", "install"),
        "TestFlight links show up in " + channel_mention("announcements") + " when a build is ready. "
        f"You can talk through builds in {channel_mention('beta-testers')}.",
    ),
    (
        ("spanish", "french", "language", "dele", "delf"),
        "Right now it's Spanish and French writing practice. "
        f"Exam prep is in the **EXAMS** section — {channel_mention('dele')}, "
        f"{channel_mention('delf')}, and {channel_mention('find-a-seat')}.",
    ),
    (
        ("journal", "entry", "privacy"),
        "Journal entries stay on your device. Cloud AI only sees what you send for a given analysis.",
    ),
    (
        ("role", "roles", "choose"),
        f"Head to {channel_mention('choose-roles')} when you get a chance — helps people know what you're working on.",
    ),
]

BUG_TEMPLATE = """If you can add:
• Device (e.g. iPhone 15, iOS 18)
• Parlance version or TestFlight build
• Language (Spanish / French)
• Steps to reproduce
• What you expected vs what happened
• A screenshot if you have one"""

FEEDBACK_TEMPLATE = """If you can add:
• What you want (one sentence)
• Why it would help your practice
• How important it is to you"""
