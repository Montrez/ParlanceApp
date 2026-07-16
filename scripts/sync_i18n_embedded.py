#!/usr/bin/env python3
"""Regenerate i18n.js `_embedded` fallbacks from locales/*.json (single source of truth).

Usage:
  python3 scripts/sync_i18n_embedded.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ROOT / "Parlance" / "web" / "locales"
I18N = ROOT / "Parlance" / "web" / "i18n.js"


def js_string(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def build_embedded(messages: dict[str, dict]) -> str:
    lines = ["  _embedded: {"]
    for lang in sorted(messages.keys()):
        lines.append(f"    {lang}: {{")
        items = messages[lang]
        keys = list(items.keys())
        for i, key in enumerate(keys):
            comma = "," if i < len(keys) - 1 else ""
            lines.append(f"      {key}: {js_string(items[key])}{comma}")
        lines.append("    },")
    # drop trailing comma on last lang block by rewriting last line
    if lines[-1] == "    },":
        lines[-1] = "    }"
    lines.append("  }")
    return "\n".join(lines)


def main() -> None:
    messages = {}
    for path in sorted(LOCALES.glob("*.json")):
        messages[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    if not messages:
        raise SystemExit(f"No locale JSON in {LOCALES}")

    text = I18N.read_text(encoding="utf-8")
    block = build_embedded(messages)
    # Replace from _embedded: { … closing }; before end of i18n object
    pattern = re.compile(r"  _embedded: \{.*?\n  \}", re.S)
    if not pattern.search(text):
        raise SystemExit("Could not find _embedded block in i18n.js")
    new_text = pattern.sub(block, text, count=1)
    I18N.write_text(new_text, encoding="utf-8")
    print(f"Synced _embedded for: {', '.join(sorted(messages))} ({sum(len(v) for v in messages.values())} keys total)")


if __name__ == "__main__":
    main()
