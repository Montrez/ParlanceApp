#!/usr/bin/env python3
"""Copy Parlance/web/ into docs/ for GitHub Pages.

Parlance/web/ is the only place you edit the journal, guides, CSS, and JS.
iOS bundles that folder. Capacitor copies that folder into Android.
docs/ is a generated twin for GitHub Pages. Do not edit app UI there.

Usage:
  python3 scripts/sync_web.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "Parlance" / "web"
DOCS = ROOT / "docs"


def main() -> int:
    if not WEB.is_dir():
        print(f"error: missing {WEB}", file=sys.stderr)
        return 1
    DOCS.mkdir(parents=True, exist_ok=True)
    copied = 0
    for src in WEB.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(WEB)
        dest = DOCS / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.read_bytes() == src.read_bytes():
            continue
        shutil.copy2(src, dest)
        copied += 1
        print(f"  {rel}")
    print(f"sync_web: {copied} file(s) updated in docs/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
