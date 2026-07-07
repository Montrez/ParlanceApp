#!/usr/bin/env python3
"""Golden regression for Parlance Coach assessed_level quality."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TRAINING_DIR))

from parlance_slm_infer import get_engine  # noqa: E402
from parlance_slm_validate import normalize_assessed_level, validate_generation_quality  # noqa: E402

LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]


def level_index(lvl: str | None) -> int | None:
    if not lvl:
        return None
    try:
        return LEVEL_ORDER.index(lvl.upper())
    except ValueError:
        return None


def load_golden(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def level_within_tolerance(
    assessed: str | None, expect: str | None, tolerance: int
) -> bool:
    if not expect:
        return True
    if assessed == expect:
        return True
    if tolerance <= 0:
        return False
    ai, ei = level_index(assessed), level_index(expect)
    if ai is None or ei is None:
        return False
    return abs(ai - ei) <= tolerance


def check_case(row: dict, result: dict, *, level_tolerance: int = 0) -> list[str]:
    errors: list[str] = []
    assessed = normalize_assessed_level(result.get("assessed_level"))
    expect = normalize_assessed_level(row.get("expect_assessed_level"))
    max_lvl = normalize_assessed_level(row.get("max_assessed_level"))
    note = row.get("notes", "")

    if expect:
        if not level_within_tolerance(assessed, expect, level_tolerance):
            errors.append(f"assessed_level={assessed!r}, expected {expect!r}")
    elif expect is None and row.get("expect_assessed_level") is None:
        # explicitly expect no level
        if assessed and row.get("allow_assessed_level"):
            pass
        elif assessed and not row.get("allow_assessed_level"):
            # optional strict: some rows allow level but prefer omit
            pass

    if max_lvl and assessed:
        if level_index(assessed) is not None and level_index(assessed) > level_index(max_lvl):
            errors.append(f"assessed_level {assessed} above max {max_lvl}")

    if not result.get("complexity_note"):
        errors.append("missing complexity_note")

    if not result.get("grammar_rule"):
        errors.append("missing grammar_rule")

    expl = str(result.get("explanation") or "").lower()
    for forbidden in row.get("forbid_in_explanation") or []:
        if forbidden.lower() in expl:
            errors.append(f"explanation must not contain {forbidden!r}")

    if row.get("expect_status") and result.get("status") != row.get("expect_status"):
        errors.append(f"status={result.get('status')!r}, expected {row.get('expect_status')!r}")

    if row.get("require_explanation_contains"):
        needle = row["require_explanation_contains"].lower()
        if needle not in expl and needle not in str(result.get("grammar_rule") or "").lower():
            errors.append(f"explanation must mention {needle!r}")

    # Generation quality checks (next_level_alt, tip, register)
    lang = row.get("lang", "es")
    gen_failures = validate_generation_quality(row.get("sentence", ""), result, lang=lang)
    for gf in gen_failures:
        # Allow individual cases to opt out of specific quality checks
        skip = row.get("skip_quality_checks") or []
        if not any(kw in gf for kw in skip):
            errors.append(gf)

    if errors:
        errors.insert(0, f"[{note}] {row.get('sentence', '')[:50]}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Run coach golden regression")
    parser.add_argument("--lang", choices=["es", "fr"], default="es")
    parser.add_argument("--golden", type=Path, default=None)
    parser.add_argument(
        "--level-tolerance",
        type=int,
        default=0,
        help="Allow assessed_level within N CEFR steps of expected (0 = exact)",
    )
    args = parser.parse_args()

    golden = args.golden or TRAINING_DIR / "golden" / f"coach_regression_{args.lang}.jsonl"
    if not golden.exists():
        print(f"Missing {golden}")
        sys.exit(1)

    engine = get_engine(args.lang)
    rows = load_golden(golden)
    failed_cases = 0

    print(f"\nCoach regression — {args.lang.upper()} ({len(rows)} cases)\n")
    if args.level_tolerance:
        print(f"  (level tolerance ±{args.level_tolerance} CEFR step(s))\n")
    for row in rows:
        sentence = row["sentence"]
        result = engine.analyze(sentence, level="")
        errs = check_case(row, result, level_tolerance=args.level_tolerance)
        assessed = result.get("assessed_level")
        status = result.get("status", "?")
        if errs:
            failed_cases += 1
            print(f"  FAIL  [{assessed or '—'}] {sentence[:55]}")
            for e in errs[1:]:
                print(f"        {e}")
        else:
            print(f"  OK    [{assessed or '—'}] {status:18} {sentence[:50]}")

    passed = len(rows) - failed_cases
    print(f"\n{passed} / {len(rows)} cases passed")
    if failed_cases:
        sys.exit(1)
    print("\nAll golden checks passed.")


if __name__ == "__main__":
    main()
