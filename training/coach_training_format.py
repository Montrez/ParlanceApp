#!/usr/bin/env python3
"""Build and migrate Parlance Coach training examples (assessed_level schema)."""

from __future__ import annotations

import json
import re
from typing import Any

from parlance_slm_validate import (
    _assessed_level_plausible,
    french_coach_system_prompt,
    french_coach_user_prompt,
    normalize_assessed_level,
    spanish_coach_system_prompt,
    spanish_coach_user_prompt,
)

USER_LEVEL_RE = re.compile(
    r"Analyze this (?:Spanish|French) sentence at (A1|A2|B1|B2|C1|C2) level:",
    re.I,
)
SENTENCE_RE = re.compile(r'"([^"]+)"\s*$')

FEEDBACK_KEYS = (
    "assessed_level",
    "complexity_note",
    "status",
    "grammar_rule",
    "explanation",
    "correction",
    "register",
    "next_level_alt",
    "target_level_alt",
    "tip",
)

DIALECT_RE = re.compile(r"expertise in (\w+) dialect", re.I)


def extract_sentence_from_user(user: str) -> str:
    m = SENTENCE_RE.search(user.strip())
    return m.group(1) if m else ""


def extract_ground_level(user: str) -> str | None:
    m = USER_LEVEL_RE.search(user)
    return normalize_assessed_level(m.group(1)) if m else None


def extract_dialect(system: str, lang: str) -> str:
    m = DIALECT_RE.search(system)
    if m:
        return m.group(1).lower()
    return "mexican" if lang == "es" else "france"


def complexity_note_for(sentence: str, level: str | None, *, uncertain: bool = False) -> str:
    wc = len(sentence.split())
    if uncertain:
        return (
            f"Mixed structures ({wc} words); vocabulary and syntax do not map cleanly to one "
            "CEFR band — assess grammar without forcing a level label."
        )
    lvl = (level or "B1").upper()
    notes = {
        "A1": f"Very short utterance ({wc} words), basic present-tense vocabulary, no subordination.",
        "A2": f"Simple structures ({wc} words); may use past or near future but little subordination.",
        "B1": f"Intermediate syntax ({wc} words); past tenses or basic subjunctive triggers may appear.",
        "B2": f"Upper-intermediate ({wc} words); subjunctive, conditionals, or richer vocabulary likely.",
        "C1": f"Advanced ({wc} words); subordination, precision vocabulary, or professional register.",
        "C2": f"Near-native complexity ({wc} words); nuanced register or dense professional phrasing.",
    }
    return notes.get(lvl, notes["B1"])


def migrate_feedback_payload(
    old: dict[str, Any],
    sentence: str,
    ground_level: str | None,
    lang: str,
) -> dict[str, Any]:
    """Map legacy assistant JSON to inference-time schema."""
    out: dict[str, Any] = {}

    for key in ("status", "grammar_rule", "explanation", "correction", "register", "tip"):
        if key in old and old[key] is not None:
            out[key] = old[key]

    out["next_level_alt"] = (
        old.get("next_level_alt")
        or old.get("c1_alternative")
        or old.get("b1_alternative")
        or old.get("next_level_alt")
    )
    out["target_level_alt"] = old.get("target_level_alt") or old.get("c1_alternative")

    if out.get("status") == "Excellent":
        out["correction"] = None

    assessed = normalize_assessed_level(old.get("assessed_level") or old.get("cefr_level"))
    if not assessed and ground_level:
        if _assessed_level_plausible(sentence, ground_level):
            assessed = ground_level

    if assessed and sentence and _assessed_level_plausible(sentence, assessed):
        out["assessed_level"] = assessed
        out["complexity_note"] = str(old.get("complexity_note") or "").strip() or complexity_note_for(
            sentence, assessed
        )
    else:
        out.pop("assessed_level", None)
        out["complexity_note"] = str(old.get("complexity_note") or "").strip() or complexity_note_for(
            sentence, None, uncertain=True
        )

    if out.get("status") not in ("Excellent", "Needs Improvement"):
        out["status"] = "Needs Improvement" if out.get("correction") else "Excellent"

    if not out.get("grammar_rule"):
        out["grammar_rule"] = "Sentence structure"
    if not out.get("explanation"):
        out["explanation"] = "See grammar rule above."

    if not out.get("target_level_alt"):
        out["target_level_alt"] = None

    return {k: v for k, v in out.items() if v is not None or k in ("correction", "target_level_alt")}


def build_training_messages(
    lang: str,
    sentence: str,
    feedback: dict[str, Any],
    *,
    dialect: str | None = None,
) -> dict[str, list[dict[str, str]]]:
    if lang == "es":
        dia = dialect or "mexican"
        system = spanish_coach_system_prompt("", dialect=dia)
        user = spanish_coach_user_prompt(sentence)
    else:
        system = french_coach_system_prompt("")
        user = french_coach_user_prompt(sentence)

    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
            {"role": "assistant", "content": json.dumps(feedback, ensure_ascii=False)},
        ]
    }


def migrate_training_example(example: dict[str, Any], lang: str) -> dict[str, Any] | None:
    messages = example.get("messages")
    if not messages or len(messages) < 3:
        return None

    system = next((m["content"] for m in messages if m.get("role") == "system"), "")
    user = next((m["content"] for m in messages if m.get("role") == "user"), "")
    assistant = next((m["content"] for m in messages if m.get("role") == "assistant"), "")

    sentence = extract_sentence_from_user(user)
    if not sentence:
        return None

    try:
        old_fb = json.loads(assistant)
    except json.JSONDecodeError:
        return None

    ground = extract_ground_level(user)
    dialect = extract_dialect(system, lang)
    feedback = migrate_feedback_payload(old_fb, sentence, ground, lang)
    return build_training_messages(lang, sentence, feedback, dialect=dialect)


def legacy_seed_to_training(row: dict[str, Any], lang: str) -> dict[str, Any]:
    """Convert Parlance/training/seed_*.jsonl flat rows to chat format."""
    sentence = row.get("sentence") or row.get("input_sentence") or ""
    if not sentence:
        raise ValueError("missing sentence")

    ground = normalize_assessed_level(row.get("level") or row.get("cefr_level"))
    feedback = {
        "status": row.get("status", "Excellent"),
        "grammar_rule": row.get("grammar_rule", ""),
        "explanation": row.get("explanation", ""),
        "correction": row.get("correction"),
        "register": row.get("register"),
        "next_level_alt": row.get("next_level_alt") or row.get("c1_alternative") or row.get("b1_alternative"),
        "target_level_alt": row.get("target_level_alt"),
        "tip": row.get("tip"),
    }
    if row.get("assessed_level") is not None or row.get("complexity_note"):
        feedback["assessed_level"] = row.get("assessed_level")
        feedback["complexity_note"] = row.get("complexity_note")
    feedback = migrate_feedback_payload(feedback, sentence, ground, lang)
    return build_training_messages(lang, sentence, feedback)
