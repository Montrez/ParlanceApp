#!/usr/bin/env python3
"""Validate shared/coach-rules/*.json — schema, sources, and regression links."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / "shared" / "coach-rules"
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
    if failed:
        sys.exit(1)
    print("\nAll coach rule packs valid.")


if __name__ == "__main__":
    main()
