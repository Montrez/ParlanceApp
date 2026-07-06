"""Role-based exam center suggestions."""
from __future__ import annotations

from discord_channel_catalog import channel_mention
from discord_exam_data import (
    DELE_COUNTRIES,
    DELF_COUNTRIES,
    EXAM_FAMILY,
    REGION_COUNTRY_VALUES,
    ROLE_TO_CHANNEL,
    SIELE_COUNTRIES,
)
from discord_exam_locations import location_note, locations_for_country


def member_exam_roles(role_names: set[str]) -> list[str]:
    order = ["DELE", "SIELE", "DELF", "DALF", "TCF"]
    return [e for e in order if e in role_names]


def member_region(role_names: set[str]) -> str | None:
    for r in REGION_COUNTRY_VALUES:
        if r in role_names:
            return r
    return None


def countries_for_exam(exam: str) -> list[dict[str, str]]:
    if exam == "SIELE":
        return SIELE_COUNTRIES
    if EXAM_FAMILY.get(exam) == "spanish":
        return DELE_COUNTRIES
    return DELF_COUNTRIES


def filter_countries_by_region(
    countries: list[dict[str, str]], region: str | None
) -> list[dict[str, str]]:
    if not region:
        return countries
    preferred = REGION_COUNTRY_VALUES.get(region, [])
    if not preferred:
        return countries
    ranked = []
    for val in preferred:
        for c in countries:
            if c["value"] == val:
                ranked.append(c)
    for c in countries:
        if c not in ranked:
            ranked.append(c)
    return ranked[:8] + [countries[-1]] if countries else ranked


def exam_channels_for_roles(exams: list[str]) -> list[str]:
    chans = []
    for e in exams:
        ch = ROLE_TO_CHANNEL.get(e)
        if ch and ch not in chans:
            chans.append(ch)
    return chans


def exam_role_followup(exams: list[str], region: str | None) -> str:
    if not exams:
        return (
            "When you pick an exam above, visit the **EXAMS** section — "
            f"each exam has its own channel with tips. {channel_mention('find-a-seat')} uses your roles to locate a center."
        )
    channels = ", ".join(channel_mention(c) for c in exam_channels_for_roles(exams))
    msg = f"Head to {channels} for prep and discussion."
    if region:
        msg += f" When you're ready to book, try {channel_mention('find-a-seat')} — it reads your region role."
    else:
        msg += f" Set a **region** role too, then {channel_mention('find-a-seat')} can narrow centers near you."
    return msg


def center_result_text(
    exam: str,
    country: dict[str, str],
    *,
    location: dict[str, str] | None = None,
    city_query: str | None = None,
) -> str:
    if location:
        place = f"{country['label']} · {location['label']}"
        note = location_note(exam, location)
    elif city_query:
        place = f"{country['label']} · {city_query.strip()}"
        note = (
            f"On the official directory, search for **{city_query.strip()}** "
            "to find the nearest authorized center."
        )
    else:
        place = country["label"]
        note = country["note"]

    return (
        f"**{exam}** — {place}\n\n"
        f"{note}\n\n"
        f"{country['url']}\n\n"
        "Confirm dates and seats with the center directly."
    )
