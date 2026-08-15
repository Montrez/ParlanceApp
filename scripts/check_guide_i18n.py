#!/usr/bin/env python3
"""Guard against shipping guide/dialect/domain content pages that don't react
to the app's interface language, and against Parlance/web/ <-> docs/ drift.

This exists because it happened twice in one session: new content pages
(guide-en.html, dialect-en.html, domain-medical.html, domain-legal.html) were
authored with hardcoded English chrome and no `guide-ui.js` wiring, so
switching the app's interface language did nothing once one of those pages
was open. See .cursor/skills/parlance-i18n/SKILL.md and GitHub issue #12.

Checks:
  1. Every Parlance/web/{guide,dialect,domain}-*.html file either:
       - includes guide-ui.js AND calls GuideUI.init( AND has >=1 data-t-*
         attribute, or
       - is explicitly listed in KNOWN_UNWIRED_LEGACY below (pre-existing
         debt, tracked on #12) — adding to this list requires a comment
         explaining why.
  2. Every file that exists under both Parlance/web/ and docs/ is
     byte-identical (docs/ is the GitHub Pages twin from sync_web.py; drift
     means Pages is stale. Android copies Parlance/web/ via Capacitor).

Usage:
  python3 scripts/check_guide_i18n.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "Parlance" / "web"
DOCS = ROOT / "docs"

# Pre-existing pages (predate the guide-ui.js convention) that still need a
# trilingual retrofit. Tracked as follow-up on issue #12. Do not add new
# entries here without a comment — new pages must ship wired correctly.
KNOWN_UNWIRED_LEGACY = {
    # Previously guide-es.html / guide-fr.html — retrofitted 2026-07-16 with
    # binary EN↔native chrome via guide-ui.js. Keep this set empty unless a
    # new legacy page is intentionally deferred.
}

CONTENT_PAGE_GLOBS = ("guide-*.html", "dialect-*.html", "domain-*.html")


def check_guide_wiring() -> list[str]:
    errors = []
    files: set[Path] = set()
    for pattern in CONTENT_PAGE_GLOBS:
        files.update(WEB.glob(pattern))

    for f in sorted(files):
        if f.name in KNOWN_UNWIRED_LEGACY:
            continue
        text = f.read_text(encoding="utf-8")
        problems = []
        if "guide-ui.js" not in text:
            problems.append("missing <script src=\"guide-ui.js\">")
        if "GuideUI.init(" not in text:
            problems.append("missing GuideUI.init(...) call")
        if "data-t-en" not in text and "data-t-en-html" not in text:
            problems.append("no data-t-en / data-t-en-html attributes found")
        if problems:
            errors.append(f"{f.relative_to(ROOT)}: {'; '.join(problems)}")
    return errors


def check_docs_mirror() -> list[str]:
    errors = []
    if not DOCS.exists():
        return errors
    for web_file in WEB.rglob("*"):
        if web_file.is_dir():
            continue
        rel = web_file.relative_to(WEB)
        docs_file = DOCS / rel
        if not docs_file.exists():
            continue  # not every web/ file has (or needs) a docs/ twin
        if web_file.read_bytes() != docs_file.read_bytes():
            errors.append(f"docs/{rel} is out of sync with Parlance/web/{rel}")
    return errors


def main() -> int:
    errors = check_guide_wiring() + check_docs_mirror()

    if errors:
        print("Guide i18n / docs-mirror check FAILED:")
        for e in errors:
            print(f"  - {e}")
        print()
        print("See .cursor/skills/parlance-i18n/SKILL.md \"Content pages whose "
              "audience isn't binary\" section for the required pattern, and "
              "mirror any Parlance/web/ change into docs/.")
        return 1

    checked = len(set().union(*(WEB.glob(p) for p in CONTENT_PAGE_GLOBS)))
    print(f"Guide i18n OK — {checked} content pages checked "
          f"({len(KNOWN_UNWIRED_LEGACY)} legacy exemptions); docs/ mirror OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
