---
name: parlance-guides
description: >-
  Keep Parlance dialect, medical, and legal guides consistent. Use when
  editing guide-*.html, dialect-*.html, domain-*.html, guide-ui.js,
  Contents, Back, guide overlay, or when deciding which language a guide
  page should speak.
---

# Parlance guides

## Language rule

Do not rewrite medical or legal books into per-language editions unless asked.

| Content | Follows |
|---|---|
| Grammar and dialect teaching (ES / FR write language) | Write language (the journal language) |
| English grammar and dialect teaching | App language (EN / ES / FR). Spanish UI = Spanish instructions for learning English. French UI = French instructions. Do not ship one combined "for ES and FR speakers" book. |
| Medical and legal teaching | App language (EN / ES / FR interface) |
| Vocab and fixed phrases | Bilingual columns (source + target stay visible) |

Practice language (what the user writes) is not the same as interface language (menus). Guide chrome uses `guide-ui.js` (`data-t-en` plus `data-t-native`, or the three-way `data-t-en` / `data-t-es` / `data-t-fr`).

## Overlay chrome

Contents and Back live inside the guide iframe. The host phone sheet must not cover them.

When a guide opens, the web layer:

1. Adds `body.guide-open`
2. Calls `closeFeedbackSheet()`
3. Shows `#guideOverlay` at z-index 400

`body.guide-open` hides `.feedback-panel` and `.feedback-sheet-backdrop`. If Contents or Back sit under FEEDBACK / PROMPTS / GUIDE, the overlay lost that contract. Fix `Parlance/web/styles.css` and `journal.js`, then `python3 scripts/sync_web.py`.

## New or edited guide pages

Follow `.cursor/skills/parlance-i18n/SKILL.md`. Wire `guide-ui.js`. Run `python3 scripts/sync_web.py` and `python3 scripts/check_guide_i18n.py`.
