#!/usr/bin/env python3
"""Narrow grammar-correction training format for the next Parlance coach.

The 0.5B professor schema (CEFR, rewrites, register, tips) taught the model
to fill a form. This format only asks: leave it alone, or make the smallest
real fix.
"""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

LANG_NAMES = {"es": "Spanish", "fr": "French", "en": "English"}

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+")
NO_ERROR_RE = re.compile(
    r"\b(pas de faute|aucune faute|no (?:error|mistake)|correct(?:e|a)?|"
    r"ne contient pas de faute|phrase correcte|sin error)\b",
    re.I,
)
WORD_RE = re.compile(r"[a-z0-9àáâäèéêëìíîïòóôöùúûüçñœæ]+", re.I)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", (text or "").strip())
    text = re.sub(r"\s+", " ", text)
    return text


def fold(text: str) -> str:
    text = unicodedata.normalize("NFD", normalize_text(text).lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^\w\s']", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_set(text: str) -> set[str]:
    return {m.group(0).lower() for m in WORD_RE.finditer(fold(text)) if len(m.group(0)) >= 2}


def token_overlap(a: str, b: str) -> float:
    ta, tb = token_set(a), token_set(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def split_sentences(text: str) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []
    parts = [p.strip() for p in SENTENCE_SPLIT_RE.split(text) if p.strip()]
    return parts or [text]


def same_sentence(a: str, b: str) -> bool:
    return fold(a) == fold(b)


def gec_system_prompt(lang: str) -> str:
    name = LANG_NAMES[lang]
    return (
        f"You are a {name} grammar coach for interpreter training. "
        "Decide if the sentence has a real grammar, spelling, agreement, or "
        "word-form error. Do not invent errors. Do not rewrite politeness, "
        "style, or meaning. Prefer the smallest correction.\n"
        "Respond with ONLY a JSON object:\n"
        "{\n"
        '  "status": "Excellent" or "Needs Improvement",\n'
        '  "explanation": "one or two sentences naming the real issue, or why it is correct",\n'
        '  "correction": null or "the minimally corrected sentence"\n'
        "}"
    )


def gec_user_prompt(lang: str, sentence: str) -> str:
    return f'Analyze this {LANG_NAMES[lang]} sentence: "{sentence}"'


def build_gec_example(
    lang: str,
    sentence: str,
    *,
    status: str,
    explanation: str,
    correction: str | None,
    source: str = "",
) -> dict[str, Any]:
    sentence = normalize_text(sentence)
    if status == "Excellent":
        correction = None
    elif correction:
        correction = normalize_text(correction)
    feedback = {
        "status": status,
        "explanation": normalize_text(explanation),
        "correction": correction,
    }
    row: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": gec_system_prompt(lang)},
            {"role": "user", "content": gec_user_prompt(lang, sentence)},
            {"role": "assistant", "content": json.dumps(feedback, ensure_ascii=False)},
        ]
    }
    if source:
        row["source"] = source
    return row


def pair_to_example(
    lang: str,
    source_sentence: str,
    target_sentence: str,
    *,
    explanation: str = "",
    source: str = "",
    min_overlap: float = 0.55,
    max_words: int = 80,
) -> dict[str, Any] | None:
    src = normalize_text(source_sentence)
    tgt = normalize_text(target_sentence)
    if not src or not tgt:
        return None
    if len(src.split()) > max_words or len(tgt.split()) > max_words:
        return None
    if same_sentence(src, tgt):
        return build_gec_example(
            lang,
            src,
            status="Excellent",
            explanation=explanation or "The sentence is already correct. Leave it unchanged.",
            correction=None,
            source=source,
        )
    if token_overlap(src, tgt) < min_overlap:
        return None
    if NO_ERROR_RE.search(explanation) and token_overlap(src, tgt) < 0.85:
        return None
    return build_gec_example(
        lang,
        src,
        status="Needs Improvement",
        explanation=explanation or "Minimal correction of a real learner error.",
        correction=tgt,
        source=source,
    )


def seed_row_to_gec(row: dict[str, Any], lang: str, source: str = "parlance_seed") -> dict[str, Any] | None:
    sentence = normalize_text(str(row.get("sentence") or row.get("input_sentence") or ""))
    if not sentence:
        return None
    status = row.get("status") or (
        "Needs Improvement" if row.get("correction") else "Excellent"
    )
    if status not in ("Excellent", "Needs Improvement"):
        status = "Needs Improvement" if row.get("correction") else "Excellent"
    explanation = str(row.get("explanation") or row.get("grammar_rule") or "").strip()
    correction = row.get("correction")
    if status == "Excellent":
        correction = None
    return build_gec_example(
        lang,
        sentence,
        status=status,
        explanation=explanation or "See correction.",
        correction=None if correction in (None, "", "null") else str(correction),
        source=source,
    )


def extract_user_sentence(example: dict[str, Any]) -> str:
    for msg in example.get("messages", []):
        if msg.get("role") != "user":
            continue
        content = msg.get("content") or ""
        if '"' in content:
            return content[content.index('"') + 1 : content.rindex('"')].strip()
    return ""
