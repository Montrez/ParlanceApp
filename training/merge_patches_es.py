#!/usr/bin/env python3
"""
Convert training_patches_es.jsonl into the assessed_level messages schema
and write to data/spanish/patches_es_20260616.jsonl.

Patch types handled:
  y_chain_upgrade  — y-chain fragment sentences + connector upgrades
  bad_alt          — porque-fragment negative examples (bad_alt as input)
  expected_register (informal/formal/voseo) — register labelling examples

Run:
    python merge_patches_es.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TRAINING_DIR))

from coach_training_format import build_training_messages  # noqa: E402

PATCHES_IN = TRAINING_DIR / "training_patches_es.jsonl"
OUT_FILE = TRAINING_DIR / "data" / "spanish" / "patches_es_20260616.jsonl"


def wc(sentence: str) -> int:
    return len(sentence.split())


def infer_level(sentence: str) -> str:
    n = wc(sentence)
    if n <= 5:
        return "A1"
    if n <= 9:
        return "A2"
    return "B1"


def complexity_note(sentence: str, level: str) -> str:
    n = wc(sentence)
    notes = {
        "A1": f"Very short utterance ({n} words), basic vocabulary, minimal subordination.",
        "A2": f"Simple structure ({n} words); common vocabulary with basic verb tenses.",
        "B1": f"Intermediate structure ({n} words); may include subordination or past tenses.",
    }
    return notes.get(level, f"Short utterance ({n} words).")


def convert_y_chain(row: dict) -> dict:
    """y_chain_upgrade: flag the missing-verb fragment, provide connector upgrades."""
    sentence = row["sentence"]
    level = infer_level(sentence)
    feedback = {
        "assessed_level": level,
        "complexity_note": complexity_note(sentence, level),
        "status": "Needs Improvement",
        "grammar_rule": "Verb omission / y-chain fragment",
        "explanation": (
            "The clause following 'y' omits a conjugated verb, leaving a noun phrase "
            "dangling without a predicate. Add a verb or replace 'y' with a sequencing connector."
        ),
        "correction": row["next_level_alt"],
        "register": "Informal (tú) — casual; use usted in professional interpreter settings.",
        "next_level_alt": row["next_level_alt"],
        "target_level_alt": row.get("target_level_alt"),
        "tip": (
            f"Strengthen with a sequencing connector: «{row['next_level_alt']}» "
            f"or at C1: «{row.get('target_level_alt', '')}»."
        ),
    }
    return build_training_messages("es", sentence, feedback, dialect="mexican")


def convert_bad_alt(row: dict) -> dict:
    """bad_alt: use the malformed porque-fragment as the input sentence."""
    bad = row["bad_alt"]
    correct = row["sentence"]
    level = infer_level(bad)
    feedback = {
        "assessed_level": level,
        "complexity_note": complexity_note(bad, level),
        "status": "Needs Improvement",
        "grammar_rule": "Porque-fragment / missing subordinate verb",
        "explanation": (
            "'Porque' introduces a subordinate clause and requires a conjugated verb. "
            "The phrase after 'porque' is a bare noun phrase with no predicate — this is not grammatical."
        ),
        "correction": correct,
        "register": "Informal (tú) — casual.",
        "next_level_alt": None,
        "target_level_alt": None,
        "tip": (
            "Use 'porque' only when you can complete the clause: "
            "«porque + subject + verb». To join two actions use 'y', 'antes de', or 'después de'."
        ),
    }
    return build_training_messages("es", bad, feedback, dialect="mexican")


def convert_register(row: dict) -> dict:
    """expected_register: label register correctly for informal/formal/voseo sentences."""
    sentence = row["sentence"]
    expected = row["expected_register"]
    dialect_hint = row.get("dialect", "")
    note = row.get("note", "")

    # Determine dialect for the system prompt
    if "voseo" in dialect_hint:
        dialect = "rioplatense"
    else:
        dialect = "mexican"

    level = infer_level(sentence)

    expected_lower = expected.lower()

    # Build register string — check voseo/informal before scanning for 'usted'
    # (informal examples also mention usted as a contrast, so order matters)
    if "voseo" in expected_lower or "voseo" in dialect_hint:
        register = (
            "Voseo (vos) — informal, regional (Argentina/Uruguay/Central America). "
            "Voseo is NOT an error; it is a valid regional dialect feature."
        )
    elif "informal" in expected_lower:
        register = (
            "Informal (tú) — appropriate for casual conversation; "
            "shift to usted in clinical, legal, or professional interpreter settings."
        )
    elif "formal" in expected_lower:
        register = (
            "Formal (usted) — appropriate for professional interpreter settings "
            "(medical, legal, social services)."
        )
    else:
        register = expected

    # Grammar rule depends on dialect/register type
    if "voseo" in dialect_hint and "formal" in dialect_hint:
        grammar_rule = "Register shift — voseo speaker using usted in formal/clinical context"
        explanation = (
            f"'{sentence}' uses usted, showing the speaker correctly shifting from their native "
            "voseo register to formal address in a clinical or professional setting."
        )
    elif "voseo" in dialect_hint:
        grammar_rule = "Register — voseo dialect (regional informal address)"
        explanation = (
            f"'{sentence}' uses the voseo verb form, which is the standard informal address "
            "in Argentina, Uruguay, and parts of Central America. This is correct and should "
            "NOT be flagged as an error or confused with incorrect tú usage."
        )
    elif "informal" in expected_lower:
        grammar_rule = "Register — informal address (tú)"
        explanation = (
            f"'{sentence}' uses tú (informal address), appropriate for casual conversation. "
            "In professional interpreter settings, shift to usted."
        )
    elif "formal" in expected_lower:
        grammar_rule = "Register — formal address (usted)"
        explanation = (
            f"'{sentence}' correctly uses usted (formal address), appropriate for professional "
            "and clinical interpreter settings."
        )
    else:
        grammar_rule = "Register — address form"
        explanation = f"'{sentence}' — {note}"

    feedback = {
        "assessed_level": level,
        "complexity_note": complexity_note(sentence, level),
        "status": "Excellent",
        "grammar_rule": grammar_rule,
        "explanation": explanation,
        "correction": None,
        "register": register,
        "next_level_alt": None,
        "target_level_alt": None,
        "tip": (
            "Interpreter tip: always match register to the clinical/legal setting. "
            "When addressing patients or officials, default to usted unless invited to use tú or vos."
        ),
    }
    return build_training_messages("es", sentence, feedback, dialect=dialect)


def main() -> None:
    if not PATCHES_IN.exists():
        print(f"ERROR: {PATCHES_IN} not found")
        sys.exit(1)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    converted = 0
    skipped = 0
    counts: dict[str, int] = {}

    with open(PATCHES_IN, encoding="utf-8") as fin, open(OUT_FILE, "w", encoding="utf-8") as fout:
        for lineno, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"  line {lineno}: JSON error — {exc}")
                skipped += 1
                continue

            if row.get("issue") == "y_chain_upgrade":
                patch_type = "y_chain_upgrade"
                example = convert_y_chain(row)
            elif "bad_alt" in row:
                patch_type = "bad_alt"
                example = convert_bad_alt(row)
            elif "expected_register" in row:
                patch_type = "expected_register"
                example = convert_register(row)
            else:
                print(f"  line {lineno}: unknown patch type — skipping: {list(row.keys())}")
                skipped += 1
                continue

            fout.write(json.dumps(example, ensure_ascii=False) + "\n")
            counts[patch_type] = counts.get(patch_type, 0) + 1
            converted += 1

    print(f"Converted {converted} patches → {OUT_FILE}")
    for t, n in sorted(counts.items()):
        print(f"  {t}: {n}")
    if skipped:
        print(f"  skipped: {skipped}")


if __name__ == "__main__":
    main()
