#!/usr/bin/env python3
"""Fast regression for shared coach rules — no model, no GPU."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TRAINING_DIR))

from coach_rules import analyze_sentence, feedback_from_rules, merge_with_ai  # noqa: E402

ROOT = TRAINING_DIR.parent
REGRESSION_DIR = ROOT / "shared" / "coach-rules"


def load_cases(lang: str) -> list[dict]:
    path = REGRESSION_DIR / f"regression_{lang}.jsonl"
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def check_case(row: dict, lang: str) -> list[str]:
    errors: list[str] = []
    sentence = row["sentence"]
    ground = analyze_sentence(sentence, lang)
    fired = [i["id"] for i in ground["issues"]]
    correction = ground.get("correction") or ""

    for expect_id in row.get("expect_rules") or []:
        if expect_id not in fired:
            errors.append(f"expected rule {expect_id!r}, got {fired}")

    if row.get("expect_rules") == [] and fired:
        errors.append(f"expected no rules, got {fired}")

    for needle in row.get("expect_correction_contains") or []:
        if needle.lower() not in correction.lower():
            errors.append(f"correction missing {needle!r} (got {correction[:80]!r})")

    if row.get("expect_status"):
        fb = feedback_from_rules(sentence, lang) or merge_with_ai(
            sentence, {"status": "Excellent"}, lang
        )
        if fb.get("status") != row["expect_status"]:
            errors.append(f"status={fb.get('status')!r}, expected {row['expect_status']!r}")

    if errors:
        errors.insert(0, f"[{row.get('id')}] {row.get('notes', '')}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Run coach rules regression (deterministic)")
    parser.add_argument("--lang", choices=["es"], default="es")
    args = parser.parse_args()

    cases = load_cases(args.lang)
    failed = 0
    print(f"\nCoach rules regression — {args.lang.upper()} ({len(cases)} cases)\n")
    for row in cases:
        errs = check_case(row, args.lang)
        if errs:
            failed += 1
            print(f"  FAIL  {row['sentence'][:55]}")
            for e in errs[1:]:
                print(f"        {e}")
        else:
            print(f"  OK    {row['id']:22} {row['sentence'][:45]}")

    passed = len(cases) - failed
    print(f"\n{passed} / {len(cases)} passed")
    if failed:
        sys.exit(1)
    print("\nAll coach rule checks passed.")


if __name__ == "__main__":
    main()
