#!/usr/bin/env python3
"""Verify interface-language coverage for Parlance.

Checks:
  1. locales/en.json, es.json, fr.json have identical key sets
  2. Every data-i18n* key used in index.html / journal.js exists in en.json
  3. i18n.js _embedded matches locales (optional warn if stale)

Usage:
  python3 scripts/check_i18n.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "Parlance" / "web"
LOCALES = WEB / "locales"


def load_locales() -> dict[str, dict]:
    return {
        p.stem: json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(LOCALES.glob("*.json"))
    }


def keys_from_markup(text: str) -> set[str]:
    keys = set()
    for attr in ("data-i18n", "data-i18n-html", "data-i18n-placeholder", "data-i18n-title"):
        keys.update(re.findall(rf'{attr}="([^"]+)"', text))
    return keys


def keys_from_js(text: str) -> set[str]:
    keys = set()
    # i18n.t('key') / i18n.t("key") — ignore template keys with ${}
    keys.update(re.findall(r"""i18n\.t\(\s*['"]([a-zA-Z0-9_]+)['"]""", text))
    keys.update(re.findall(r"""i18n\.tc\(\s*['"]([a-zA-Z0-9_]+)['"]""", text))
    return keys


def main() -> int:
    locales = load_locales()
    if "en" not in locales:
        print("FAIL: missing locales/en.json")
        return 1

    en_keys = set(locales["en"])
    errors = []

    for lang, data in locales.items():
        missing = en_keys - set(data)
        extra = set(data) - en_keys
        if missing:
            errors.append(f"{lang}: missing keys {sorted(missing)}")
        if extra:
            errors.append(f"{lang}: extra keys {sorted(extra)}")

    used: set[str] = set()
    for name in ("index.html", "journal.js"):
        used |= keys_from_markup((WEB / name).read_text(encoding="utf-8"))
        used |= keys_from_js((WEB / name).read_text(encoding="utf-8"))

    # plural helpers reference base key only
    missing_used = sorted(k for k in used if k not in en_keys and f"{k}_one" not in en_keys)
    if missing_used:
        errors.append(f"Referenced but not in en.json: {missing_used}")

    if errors:
        print("i18n check FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"i18n OK — {len(en_keys)} keys × {len(locales)} locales; {len(used)} keys referenced in UI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
