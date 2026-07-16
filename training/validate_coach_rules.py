#!/usr/bin/env python3
"""Validate shared/coach-rules/*.json — schema, sources, regression links, and generation quality."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / "shared" / "coach-rules"
STANDARDS_DIR = ROOT / "shared" / "standards"

# Generation-quality check field names expected in regression JSONL entries.
_GQ_FIELDS = frozenset(
    {"expect_no_fragment_alt", "expect_register_contains", "expect_tip_has_example", "expect_alt_differs"}
)
REQUIRED_RULE_KEYS = ("id", "category", "priority", "detect", "issue", "grammar_rule", "source", "regression")
REQUIRED_SOURCE_KEYS = ("authority", "topic")


def load_regression_ids(lang: str) -> set[str]:
    path = RULES_DIR / f"regression_{lang}.jsonl"
    if not path.exists():
        return set()
    ids: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                ids.add(json.loads(line)["id"])
    return ids


def validate_rule(rule: dict, regression_ids: set[str]) -> list[str]:
    errors: list[str] = []
    rid = rule.get("id", "?")
    for key in REQUIRED_RULE_KEYS:
        if key not in rule:
            errors.append(f"rule {rid}: missing {key}")
    source = rule.get("source") or {}
    for key in REQUIRED_SOURCE_KEYS:
        if key not in source:
            errors.append(f"rule {rid}: source missing {key}")
    detect = rule.get("detect") or {}
    if not detect.get("pattern") and not detect.get("type"):
        errors.append(f"rule {rid}: detect.pattern required")
    elif detect.get("pattern"):
        try:
            re.compile(detect["pattern"], re.I if "i" in (detect.get("flags") or "i") else 0)
        except re.error as e:
            errors.append(f"rule {rid}: invalid detect pattern: {e}")
    for step in rule.get("repair") or []:
        try:
            re.compile(step.get("pattern", ""), re.I)
        except re.error as e:
            errors.append(f"rule {rid}: invalid repair pattern: {e}")
    for reg_id in rule.get("regression") or []:
        if reg_id not in regression_ids:
            errors.append(f"rule {rid}: regression id {reg_id!r} not in regression file")
    return errors


def validate_pack(path: Path) -> list[str]:
    errors: list[str] = []
    with path.open(encoding="utf-8") as f:
        pack = json.load(f)
    lang = pack.get("lang", path.stem)
    std_ver = pack.get("standard_version")
    if std_ver is not None:
        std_path = STANDARDS_DIR / f"{lang}-coach-standard.json"
        if std_path.exists():
            with std_path.open(encoding="utf-8") as f:
                std = json.load(f)
            if int(std.get("version") or 0) != int(std_ver):
                errors.append(
                    f"standard_version {std_ver} does not match {std_path.name} version {std.get('version')}"
                )
    regression_ids = load_regression_ids(lang)
    seen: set[str] = set()
    for rule in pack.get("rules") or []:
        rule["lang"] = lang
        rid = rule.get("id")
        if rid in seen:
            errors.append(f"duplicate rule id {rid}")
        seen.add(rid)
        errors.extend(validate_rule(rule, regression_ids))
    return errors


def _load_generation_quality_validator():
    """Import generation-quality helpers at call time to avoid circular imports
    when the training/ directory is not on sys.path.

    Returns (validate_generation_quality, heuristic_feedback, french_heuristic_feedback).
    """
    import importlib.util
    training_dir = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location(
        "parlance_slm_validate", training_dir / "parlance_slm_validate.py"
    )
    if spec is None or spec.loader is None:
        return None, None, None
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(training_dir))
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    except Exception:
        return None, None, None
    return (
        getattr(mod, "validate_generation_quality", None),
        getattr(mod, "heuristic_feedback", None),
        getattr(mod, "french_heuristic_feedback", None),
    )


def validate_regression_generation_quality(lang: str) -> list[str]:
    """Run generation-quality checks against regression JSONL entries that carry
    the new quality-check fields (expect_no_fragment_alt, expect_register_contains,
    expect_tip_has_example, expect_alt_differs).

    Uses heuristic_feedback() / french_heuristic_feedback() as a deterministic
    model stand-in so that checks can run on every CI pass without a live model
    checkpoint.
    """
    path = RULES_DIR / f"regression_{lang}.jsonl"
    if not path.exists():
        return []

    validate_gq, heuristic_fb, french_heuristic_fb = _load_generation_quality_validator()
    if validate_gq is None or heuristic_fb is None:
        return ["parlance_slm_validate.py could not be imported — skipping generation quality checks"]

    errors: list[str] = []
    with path.open(encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            case = json.loads(raw)
            # Only check entries that declare at least one generation-quality field.
            if not _GQ_FIELDS.intersection(case):
                continue

            sentence = case.get("sentence", "")
            case_id = case.get("id", "?")
            if lang == "fr" and french_heuristic_fb is not None:
                result = french_heuristic_fb(sentence, "")
            else:
                result = heuristic_fb(sentence, "")

            gq_failures = validate_gq(sentence, result, lang)

            # Cross-check individual expect_ flags against the heuristic result.
            nla = result.get("next_level_alt") or ""
            tip = result.get("tip") or ""
            register = result.get("register") or ""

            if case.get("expect_no_fragment_alt") and any(
                "porque-fragment" in f for f in gq_failures
            ):
                errors.append(f"[{case_id}] FAIL expect_no_fragment_alt: next_level_alt is a fragment")

            if case.get("expect_alt_differs") and any(
                "verbatim copy" in f for f in gq_failures
            ):
                errors.append(f"[{case_id}] FAIL expect_alt_differs: next_level_alt is verbatim")

            if case.get("expect_tip_has_example") and any(
                "tip lacks" in f for f in gq_failures
            ):
                errors.append(f"[{case_id}] FAIL expect_tip_has_example: tip={tip!r}")

            if "expect_register_contains" in case:
                needle = str(case["expect_register_contains"]).lower()
                if needle not in register.lower():
                    errors.append(
                        f"[{case_id}] FAIL expect_register_contains={needle!r}: register={register!r}"
                    )

    return errors


def main() -> None:
    failed = False
    for path in sorted(RULES_DIR.glob("*.json")):
        errs = validate_pack(path)
        if errs:
            failed = True
            print(f"\n{path.name} — INVALID")
            for e in errs:
                print(f"  • {e}")
        else:
            n = len(json.loads(path.read_text(encoding="utf-8")).get("rules", []))
            print(f"{path.name} — OK ({n} rules)")

    # Generation-quality regression checks (deterministic, no live model needed).
    # Failures here are blocking — same as schema / rule-pack validation.
    for lang in ("es", "fr"):
        gq_errs = validate_regression_generation_quality(lang)
        reg_path = RULES_DIR / f"regression_{lang}.jsonl"
        if reg_path.exists():
            with reg_path.open(encoding="utf-8") as f:
                gq_count = sum(
                    1 for line in f
                    if line.strip() and _GQ_FIELDS.intersection(json.loads(line))
                )
        else:
            gq_count = 0
        if gq_errs:
            failed = True
            print(f"\nGeneration quality FAILED [{lang}] ({len(gq_errs)}/{gq_count} cases):")
            for e in gq_errs:
                print(f"  • {e}")
        elif gq_count:
            print(f"Generation quality checks [{lang}] — OK ({gq_count} cases)")

    if failed:
        sys.exit(1)
    print("\nAll coach rule packs valid.")


if __name__ == "__main__":
    main()
