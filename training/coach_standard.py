"""Parlance Coach Standard — normative Spanish/French spec shared by training, inference, and web."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_STANDARDS_DIR = Path(__file__).resolve().parent.parent / "shared" / "standards"
_CACHE: dict[str, dict[str, Any]] = {}


def load_standard(lang: str = "es") -> dict[str, Any]:
    key = "fr" if lang == "fr" else "es"
    if key in _CACHE:
        return _CACHE[key]
    path = _STANDARDS_DIR / f"{key}-coach-standard.json"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    _CACHE[key] = data
    return data


def standard_prompt_block(lang: str = "es") -> str:
    """Text block injected into every coach system prompt (training + inference)."""
    std = load_standard(lang)
    if not std:
        return ""

    lines = [
        f"=== {std.get('name', 'Parlance Coach Standard').upper()} ===",
        f"Normative authority: {std.get('normative_authority', 'RAE')}",
        f"CEFR: {std.get('cefr_framework', 'MCER')}",
        "",
        str(std.get("role", "")).strip(),
        "",
        "PRINCIPLES (you must know and apply these):",
    ]
    for p in std.get("principles") or []:
        lines.append(f"- {p}")

    lines.extend(["", "NON-NEGOTIABLE ERRORS (always Needs Improvement + full correction):"])
    for e in std.get("non_negotiable_errors") or []:
        lines.append(f"- {e}")

    if std.get("excellent_means"):
        lines.extend(["", f"Excellent: {std['excellent_means']}"])
    if std.get("needs_improvement_means"):
        lines.append(f"Needs Improvement: {std['needs_improvement_means']}")
    if std.get("interpreter_register"):
        lines.append(f"Register: {std['interpreter_register']}")

    lines.append("")
    return "\n".join(lines)


def standard_version(lang: str = "es") -> int:
    return int(load_standard(lang).get("version") or 0)
