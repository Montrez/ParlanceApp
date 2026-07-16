"""Shared coach rules — loads shared/coach-rules/*.json (same source as web)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_RULES_DIR = Path(__file__).resolve().parent.parent / "shared" / "coach-rules"
_CACHE: dict[str, dict[str, Any]] = {}

_PLACEHOLDER_CORRECTIONS = frozenset(
    {"corrected sentence", "correction", "n/a", "null", "none"}
)

# Short but valid corrections in these languages that must not be treated as
# placeholders (e.g. a single accented word or a fixed grammatical particle).
_SHORT_CORRECTION_ALLOW_WORDS = frozenset(
    {
        # French function words / particles common in short corrections.
        "où", "ou", "à", "a", "là", "la", "du", "des", "de", "d'",
        "c'est", "il est", "elle est", "ne", "pas", "que", "qui",
        "j'ai", "j'aime", "tu", "vous", "je", "il", "elle", "on",
    }
)


_SUPPORTED_LANGS = frozenset({"es", "fr", "en"})


def load_rules(lang: str = "es") -> dict[str, Any]:
    key = lang if lang in _SUPPORTED_LANGS else "es"
    if key in _CACHE:
        return _CACHE[key]
    path = _RULES_DIR / f"{key}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Coach rule pack missing for lang={key!r}: expected {path}. "
            "No silent empty rule pack is allowed — create the pack or fix the path."
        )
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
    require_pat = detect.get("require_pattern")
    if require_pat and not re.search(require_pat, text, flags):
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
    if (
        re.search(r"\btodo\b", norm)
        and re.search(r"\baplicaci", norm)
        and not re.search(r"\btoda\b", norm)
        and "todo_before_feminine_noun" not in seen
    ):
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
    changed = correction.strip() != sentence.strip()
    return {
        "issues": issues,
        "correction": correction if changed else None,
        "has_errors": bool(issues) or changed,
    }


def _is_placeholder_correction(text: str | None, lang: str = "es") -> bool:
    if not text or not str(text).strip():
        return True
    t = str(text).strip()
    lower = t.lower().rstrip(".:")
    # Allow short but valid corrections (e.g. "Comí ayer", "¿Cómo está?", "j'aime", "où")
    if len(t) < 5:
        return lower not in _SHORT_CORRECTION_ALLOW_WORDS
    if lower in _PLACEHOLDER_CORRECTIONS:
        return True
    # Reject strings that look like English labels or pure ASCII with no
    # target-language content (function-word allowlist differs by language).
    if len(t) < 20 and re.fullmatch(r"[a-zA-Z0-9 .,;:'\-]+", t):
        if lang == "fr":
            has_lang_words = re.search(
                r"\b(le|la|les|un|une|que|qui|pour|par|est|c'est|il|elle|je|tu|vous|de|du|des|ne|pas)\b",
                t,
                re.I,
            )
        else:
            has_lang_words = re.search(
                r"\b(el|la|los|las|un|una|que|por|para|es|son|fue|fui|con|sin|muy)\b", t, re.I
            )
        if not has_lang_words:
            return True
    return False


def _explanation_covers(issue: dict[str, Any], explanation: str) -> bool:
    expl = explanation or ""
    lower = expl.lower()
    iid = issue.get("id", "")
    if iid in (
        "todo_toda",
        "todo_before_feminine_noun",
        "todo_por_la_aplicacion",
        "todo_la_aplicacion",
    ):
        if re.search(r"\btodo\s+la\s+aplicaci", expl, re.I):
            return False
        if re.search(r"\btodo\s+por\s+la\s+aplicaci", expl, re.I):
            return False
        return bool(re.search(r"\btoda\s+la\s+aplicaci", expl, re.I)) or (
            "toda" in lower and "feminine" in lower
        )
    if iid.startswith("tenemos_que"):
        if re.search(r"\btenamos\b", expl, re.I):
            return False
        return "tenemos que" in lower
    return any(str(m).lower() in lower for m in issue.get("mention") or [])


def _grammar_rule_is_generic(text: str) -> bool:
    """Return True when a grammar_rule string is too vague to be useful."""
    if not text or len(text.strip()) < 8:
        return True
    lower = text.strip().lower()
    generic_phrases = (
        "grammar rule",
        "sentence structure",
        "general grammar",
        "spanish grammar",
        "french grammar",
        "language rule",
        "grammar and style",
        "grammar and usage",
        "correct grammar",
        "basic grammar",
        "improve grammar",
    )
    return any(p in lower for p in generic_phrases)


def _register_note(sentence: str, lang: str = "es") -> str:
    norm = _normalize(sentence)
    if lang == "fr":
        if re.search(r"\b(madame|monsieur|vous|veuillez)\b", norm) and not re.search(r"\btu\b", norm):
            return (
                "Formal vous with vocative «madame/monsieur» — keep second-person plural verb forms "
                "(«êtes», not «es») in professional settings."
            )
        if re.search(r"\b(tu|toi|copain|copine|ami)\b", norm) and not re.search(r"\bvous\b", norm):
            return "Informal tu/familiar address — match the relationship in your interpreting scenario."
        if re.search(r"\btu\b", norm) and re.search(r"\bvous\b", norm):
            return "Register mismatch — do not mix tu and vous for the same interlocutor; pick one and keep it consistent."
        return "Match tu/vous and formality to the setting (clinical, legal, or casual)."
    if re.search(r"\b(senor|senora|usted)\b", norm) and "tu " not in norm:
        return (
            "Formal usted with vocative «señor/señora» — keep third-person verb forms "
            "(«está», not «estás») in professional settings."
        )
    if re.search(r"\b(te|tu|amor|carino)\b", norm):
        return "Informal tú/familiar address — match the relationship in your interpreting scenario."
    return "Match tú/usted and formality to the setting (clinical, legal, or casual)."


def _tip_for_issues(
    sentence: str, issues: list[dict[str, Any]], correction: str | None, *, lang: str = "es"
) -> str:
    from coach_tips import tip_for_improvement

    return tip_for_improvement(sentence, issues, correction, lang=lang)


def feedback_from_rules(sentence: str, lang: str = "es") -> dict[str, Any] | None:
    """Full rule-based feedback when the model fails or is bypassed."""
    ground = analyze_sentence(sentence, lang)
    if not ground["has_errors"]:
        return None
    issues = ground["issues"]
    grammar_parts = list(dict.fromkeys(i["grammar_rule"] for i in issues if i.get("grammar_rule")))
    pack = load_rules(lang)
    bullets = "\n".join(f"• {i['issue']}" for i in issues)
    correction = ground["correction"]
    return {
        "status": "Needs Improvement",
        "grammar_rule": "; ".join(grammar_parts) or pack.get("grammar_rule_default", ""),
        "explanation": f"Issues in your sentence:\n{bullets}",
        "correction": correction,
        "register": _register_note(sentence, lang),
        "tip": _tip_for_issues(sentence, issues, correction, lang=lang),
        "_coach_repaired": True,
        "_coach_rules": [i["id"] for i in issues],
    }


def merge_with_ai(sentence: str, feedback: dict[str, Any], lang: str = "es") -> dict[str, Any]:
    """Apply shared rules on top of any provider JSON."""
    if feedback.get("_coach_repaired"):
        return feedback

    out = dict(feedback)
    ground = analyze_sentence(sentence, lang)
    if not ground["has_errors"]:
        return out

    missed = [i for i in ground["issues"] if not _explanation_covers(i, str(out.get("explanation") or ""))]
    corr = str(out.get("correction") or "").strip()
    corr_bad = (
        _is_placeholder_correction(corr, lang)
        or detect_issues(corr, lang)
        or (
            re.search(r"\btodo\b", corr, re.I)
            and re.search(r"\baplicaci", corr, re.I)
            and not re.search(r"\btoda\b", corr, re.I)
        )
    )

    if str(out.get("explanation") or ""):
        out["explanation"] = apply_repairs(str(out["explanation"]), lang)
    if _is_placeholder_correction(corr, lang):
        out.pop("correction", None)

    out["status"] = "Needs Improvement"

    if missed:
        bullets = "\n".join(f"• {i['issue']}" for i in missed)
        header = "Issues in your sentence:" if len(missed) == len(ground["issues"]) else "Also fix:"
        expl = str(out.get("explanation") or "").strip()
        out["explanation"] = f"{expl}\n\n{header}\n{bullets}".strip() if expl else f"{header}\n{bullets}"

    if ground["correction"] and (corr_bad or not out.get("correction")):
        out["correction"] = ground["correction"]

    grammar_parts = list(dict.fromkeys(i["grammar_rule"] for i in ground["issues"] if i.get("grammar_rule")))
    rule_grammar = "; ".join(grammar_parts) or load_rules(lang).get("grammar_rule_default", "")
    if _grammar_rule_is_generic(str(out.get("grammar_rule") or "")) or len(str(out.get("grammar_rule") or "")) < 12:
        out["grammar_rule"] = rule_grammar
    elif grammar_parts and not any(g.lower() in str(out.get("grammar_rule") or "").lower() for g in grammar_parts):
        out["grammar_rule"] = rule_grammar

    out["_coach_rules"] = [i["id"] for i in ground["issues"]]
    out["_coach_enhanced"] = True
    if ground["correction"]:
        out["tip"] = _tip_for_issues(sentence, ground["issues"], ground["correction"], lang=lang)
        out["register"] = _register_note(sentence, lang)
    return out
