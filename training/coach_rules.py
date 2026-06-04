"""Shared coach rules — loads shared/coach-rules/*.json (same source as web)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_RULES_DIR = Path(__file__).resolve().parent.parent / "shared" / "coach-rules"
_CACHE: dict[str, dict[str, Any]] = {}


def load_rules(lang: str = "es") -> dict[str, Any]:
    key = "fr" if lang == "fr" else "es"
    if key in _CACHE:
        return _CACHE[key]
    path = _RULES_DIR / f"{key}.json"
    if not path.exists():
        return {"rules": [], "feminine_nouns": []}
    with path.open(encoding="utf-8") as f:
        pack = json.load(f)
    _CACHE[key] = pack
    return pack


def _normalize(text: str) -> str:
    import unicodedata

    t = unicodedata.normalize("NFD", text.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _rule_matches(text: str, rule: dict[str, Any]) -> bool:
    detect = rule.get("detect") or {}
    flags = re.I if "i" in (detect.get("flags") or "i") else 0
    unless = detect.get("unless")
    if unless and unless in text:
        return False
    unless_pat = detect.get("unless_pattern")
    if unless_pat and re.search(unless_pat, text, flags):
        return False
    pattern = detect.get("pattern")
    if pattern:
        return bool(re.search(pattern, text, flags))
    return False


def detect_issues(text: str, lang: str = "es") -> list[dict[str, Any]]:
    pack = load_rules(lang)
    matched: list[dict[str, Any]] = []
    seen: set[str] = set()
    rules = sorted(pack.get("rules") or [], key=lambda r: r.get("priority", 99))
    for rule in rules:
        rid = rule.get("id", "")
        if rid in seen:
            continue
        if _rule_matches(text, rule):
            matched.append(
                {
                    "id": rid,
                    "category": rule.get("category"),
                    "issue": rule.get("issue"),
                    "mention": rule.get("mention") or [],
                    "grammar_rule": rule.get("grammar_rule"),
                }
            )
            seen.add(rid)
    norm = _normalize(text)
    if re.search(r"\btodo\b", norm) and re.search(r"\baplicaci", norm) and not re.search(
        r"\btoda\b", norm
    ):
        if "todo_before_feminine_noun" not in seen:
            matched.append(
                {
                    "id": "todo_before_feminine_noun",
                    "category": "agreement",
                    "issue": "«Aplicación» is feminine — use «toda la aplicación», not «todo».",
                    "mention": ["toda la aplicación", "feminine todo/toda"],
                    "grammar_rule": "Gender agreement (todo/toda + feminine noun)",
                }
            )
    return matched


def apply_repairs(text: str, lang: str = "es") -> str:
    pack = load_rules(lang)
    c = text.strip()
    rules = sorted(pack.get("rules") or [], key=lambda r: r.get("priority", 99))
    for rule in rules:
        if not _rule_matches(c, rule):
            continue
        for step in rule.get("repair") or []:
            pattern = step.get("pattern", "")
            replace = step.get("replace", "")
            flags_str = step.get("flags") or "gi"
            flags = re.I if "i" in flags_str else 0
            count = 1 if step.get("once") else 0
            try:
                c = re.sub(pattern, replace, c, count=count, flags=flags)
            except re.error:
                continue
    return re.sub(r"\s+", " ", c).strip()


def analyze_sentence(sentence: str, lang: str = "es") -> dict[str, Any]:
    issues = detect_issues(sentence, lang)
    correction = apply_repairs(sentence, lang)
    sent_norm = _normalize(sentence)
    corr_norm = _normalize(correction)
    return {
        "issues": issues,
        "correction": correction if corr_norm != sent_norm else None,
        "has_errors": bool(issues) or corr_norm != sent_norm,
    }


def merge_with_ai(sentence: str, feedback: dict[str, Any], lang: str = "es") -> dict[str, Any]:
    """Apply shared rules on top of any provider JSON (mirrors web coach-rules-engine.js)."""
    out = dict(feedback)
    ground = analyze_sentence(sentence, lang)
    if not ground["has_errors"]:
        return out

    out["status"] = "Needs Improvement"
    missed = [i for i in ground["issues"] if i["issue"] not in str(out.get("explanation") or "")]
    if missed:
        bullets = "\n".join(f"• {i['issue']}" for i in missed)
        header = "Issues in your sentence:" if len(missed) == len(ground["issues"]) else "Also fix:"
        expl = str(out.get("explanation") or "").strip()
        out["explanation"] = f"{expl}\n\n{header}\n{bullets}".strip() if expl else f"{header}\n{bullets}"

    corr = str(out.get("correction") or "").strip()
    if ground["correction"] and (len(corr) < 15 or "corrected sentence" in corr.lower()):
        out["correction"] = ground["correction"]
    elif ground["correction"] and re.search(r"\btodo\b", corr, re.I) and re.search(
        r"\baplicaci", corr, re.I
    ) and not re.search(r"\btoda\b", corr, re.I):
        out["correction"] = ground["correction"]

    out["_coach_rules"] = [i["id"] for i in ground["issues"]]
    out["_coach_enhanced"] = True
    return out
