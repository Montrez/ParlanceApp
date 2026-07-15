# Adding a practice language

This is the one system for adding a new practice language to Parlance (e.g.
German, Portuguese). If you're doing this by hand-editing files or copying
an existing language's files and search-replacing, stop — that's how the
codebase ended up with three different, drifted color systems and two
different HTML class vocabularies for the same components (fixed in the PR
that added this doc; see "Why this exists" below). Use the scripts.

This doc is scoped to *practice* languages (Spanish, French, and whatever's
next) — the language the user is learning to write in. That's a different
concern from the app's *interface* language (the EN/ES/FR the buttons and
menus are in), which is `Parlance/web/locales/*.json` + `i18n.js` and isn't
touched by anything below.

## The short version

```bash
# 1. Scaffold every file this language needs.
python3 scripts/new_language_scaffold.py de "Deutsch" \
    --coach-role German --exam-key goethe

# 2. Wire the new files into the Xcode project (native app bundle).
python3 scripts/xcode_add_web_resources.py guide-de.html dialect-de.html \
    coach-standard-de.js

# 3. Write the actual content (the script only generates TODO-marked stubs).
#    See "What you still have to write" below.

# 4. Verify, then commit.
xcodebuild -list -project Parlance.xcodeproj   # sanity-check the project still parses
```

Read the full checklist `new_language_scaffold.py` prints at the end — it's
specific to the language code you passed and tells you exactly which files
and which RAG_KNOWLEDGE keys still need real content.

## The system, and why it's shaped this way

Every practice language needs the same handful of things, and every one of
them used to be a place a new language could silently drift from the others:

| Concern | Single source of truth | Generated / kept in sync by |
|---|---|---|
| Language metadata (name, coach role, exam key, model folder) | `Parlance/web/languages.js` (web) + `Parlance/LanguageRegistry.swift` (native) | `new_language_scaffold.py` writes the `languages.js` row; you add the Swift row by hand (native model bundling is manual — see step 6 of the script's checklist) |
| Colors, for **every** guide/dialect page | `design/theme.json` → `content_tokens` | `scripts/generate_theme.py` generates `Parlance/web/content-theme.css` (+ `docs/` mirror) |
| Guide/dialect page structure & components (sidebar, nav badges, level pills, rule boxes, tables, etc.) | `Parlance/web/content-guide.css` — **one file**, shared by every language's guide and dialect pages | Hand-maintained; new components go here, never into a page's own `<style>` |
| Guide/dialect page *content* (the actual grammar rules, regional profiles, etc.) | `Parlance/web/guide-XX.html` / `dialect-XX.html` per language | `new_language_scaffold.py` generates the *shell* with TODO stubs; a human writes the real content |
| RAG knowledge (grammar rules, exam info, medical/legal terminology, trigger words) | `Parlance/web/rag-knowledge.js` | `new_language_scaffold.py` inserts TODO stubs at the right keys; a human fills them in |
| Coach standard (register/tone rules fed to the AI) | `Parlance/web/coach-standard-XX.js` | `new_language_scaffold.py` generates a TODO stub |
| Native app bundling (Xcode resource registration) | `Parlance.xcodeproj/project.pbxproj` | `scripts/xcode_add_web_resources.py` — never hand-edit `project.pbxproj` for this |

### Why this exists

Before this system, `guide-es.html` and `guide-fr.html` each had their own
embedded `<style>` block: two separate copies of the same ~15 color
variables, with different *names* for the same concepts (`--accent2` in one,
`--green` in the other), different *values* for the dark-mode palette (one
file's dark-mode fix didn't get applied to the other), and different CSS
*class names* for the same UI component (`.tw-blue` vs `.trigger.blue`,
`.nbadge` vs `.nav-badge`, `.intro-band` vs `.intro-box`, ...). Every fix had
to be re-discovered and re-applied per file, and a new language would have
had to pick a naming convention out of thin air.

Now:

- **Colors** come from exactly one place (`design/theme.json`'s
  `content_tokens`), generated into `content-theme.css`. A new hue or a dark
  mode contrast fix happens once, in one file, and every language's guide and
  dialect pages pick it up automatically because they all `<link>` the same
  generated file.
- **Structure** (the sidebar, nav badges, level pills, rule/warn boxes,
  tables, the region picker, everything) lives in exactly one stylesheet,
  `content-guide.css`, using one class vocabulary. A guide page for language
  `XX` and a dialect page for language `XX` are just HTML content files that
  `<link>` the same two stylesheets — no per-language CSS, ever.
- **Per-language accenting** (which color is "primary" for language `XX`) is
  a single CSS class on `<body>`: `lang-XX`. Spanish is red (the default —
  no override needed), French is blue (`body.lang-fr` overrides in
  `content-guide.css`). Adding a third primary color for a new language is a
  few lines in `content-guide.css`, not a new copy of anything.

If you ever find yourself about to add a `<style>` block to a guide/dialect
HTML file, or copy-paste an existing language's page as a starting point for
a new one instead of running the scaffold script — that's the smell this
system exists to prevent. Add the component to `content-guide.css` instead,
or extend the scaffold script's template.

## What the scaffold script does for you

`scripts/new_language_scaffold.py <code> "<name>" [options]`:

1. Adds a row to `languages.js`'s `PARLANCE_LANGUAGES` registry.
2. Generates `guide-XX.html` and `dialect-XX.html` — correct `<head>`
   (linking `content-theme.css` + `content-guide.css`, nothing else), correct
   `<body class="guide lang-XX">` / `<body class="dialect lang-XX">`, and a
   TODO-marked skeleton using the canonical class names (`nav-section-label`,
   `nav-badge`, `level-pill`, `rule-box`, `intro-box`, `region-card`, etc.) —
   see `Parlance/web/content-guide.css`'s top comment for the full component
   list.
3. Adds TODO stubs to `rag-knowledge.js` (grammar, exam, medical/legal
   terminology, trigger words).
4. Generates a TODO stub `coach-standard-XX.js` (and, with `--with-rules`, an
   empty `coach-rules-XX.js`).
5. Wires `index.html`: `<option>` entries and the new `<script>` tag(s).
6. Mirrors every file into `docs/` (GitHub Pages), byte-identical to
   `Parlance/web/`, per repo convention.
7. Validates: runs `node --check` on generated/patched JS, checks generated
   HTML tags balance.
8. Prints a checklist of what's still manual (see below).

Flags:

- `--coach-role "English name"` — used in AI prompts (e.g. "German"). Defaults to `<name>`.
- `--exam-key <key>` — exam registry key (e.g. `goethe`, `dele`, `delf`). Defaults to `<code>-exam`.
- `--on-device` — only pass this once a bundled MLX model for this language actually exists.
- `--with-rules` — also generate an empty `coach-rules-XX.js`. Optional; French ships without one (the rules engine just skips rule-based detection for languages that don't have one).
- `--force` — overwrite already-generated files for this code (safe to rerun before you've started writing real content; **don't** rerun with `--force` after you've written content, you'll lose it).
- `--dry-run` — print what would happen, write nothing.

It is **not** safe to hand-edit-then-rerun the script's outputs and expect
them to merge — steps 1, 3, 5 patch existing shared files
(`languages.js`, `rag-knowledge.js`, `index.html`) by finding an exact
anchor and inserting next to it. If you need to change something the script
already generated, edit the generated file directly from then on.

## What you still have to write (the script always prints this, specific to your language)

1. Real content in `guide-XX.html` and `dialect-XX.html` (and their `docs/`
   mirrors — keep them byte-identical; copy, don't hand-diverge).
2. Real register/tone rules in `coach-standard-XX.js`.
3. Real content for the `rag-knowledge.js` stubs the script inserted.
4. A `<div class="lang-switch">` cross-link in the *other* existing
   `dialect-*.html` files pointing at the new one (and vice versa) — the
   script only wires the file it creates, not the ones that already exist.
5. If this language should also be an *interface* language (not just
   something to practice): `locales/XX.json` + an `_embedded` fallback in
   `i18n.js`. Unrelated to everything else here.
6. If/when you want an on-device Parlance Coach model: bundle MLX weights,
   add a row to `Parlance/LanguageRegistry.swift`, flip `hasOnDeviceModel` to
   `true` in `languages.js`, and follow issue #15's training-pipeline plan.
7. Xcode wiring — run `scripts/xcode_add_web_resources.py` (see below).
8. If you want a third "primary accent" color (a language that shouldn't be
   red like Spanish or blue like French): add a `body.lang-XX { ... }`
   override block in `content-guide.css` next to the existing
   `body.lang-fr` one, following the same pattern (nav-item.active,
   sidebar-logo h1, warn-box, back-btn).

## Xcode wiring (`scripts/xcode_add_web_resources.py`)

This project uses classic, explicit `PBXFileReference`/`PBXBuildFile` entries
in `project.pbxproj` (not Xcode 16's folder-synchronized groups), so every
web file the native app loads via `WKWebView` has to be registered in four
different list-like sections of that file. Doing this by hand means
hand-rolling UUIDs across four places — this is exactly how `theme.css`
shipped for a while without ever being wired into the app bundle, and how
the project ended up with two dead, misnamed `"locales 2"` placeholder
groups. Don't hand-edit `project.pbxproj` for this; run:

```bash
python3 scripts/xcode_add_web_resources.py guide-XX.html dialect-XX.html \
    coach-standard-XX.js [coach-rules-XX.js]
```

It's idempotent (already-registered paths are skipped, not duplicated) and
validates the result with `plutil -lint` before writing, refusing to leave a
broken `project.pbxproj` on disk. Follow up with
`xcodebuild -list -project Parlance.xcodeproj` and a real build before
committing.

## Regenerating the theme

If you change a color in `design/theme.json` (either the app-shell `tokens`
or the guide/dialect `content_tokens`), regenerate everything with:

```bash
python3 scripts/generate_theme.py
```

This writes `Parlance/web/theme.css`, `Parlance/web/content-theme.css` (+
`docs/` mirrors of both), and the native Xcode `.colorset` assets. Never
hand-edit any of those generated files — they say so at the top, and your
edit will be silently overwritten the next time someone runs the generator.
Run `python3 scripts/generate_theme.py --check` in CI-like contexts to catch
a `theme.json` edit that wasn't followed by regenerating.
