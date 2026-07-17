# Astro i18n pilot — findings

Scope: migrate one real production page (`Parlance/web/domain-medical.html`) from the
`data-t-en` / `data-t-es` / `data-t-fr` attribute pattern + `guide-ui.js` client-side
toggle to Astro content collections + built-in i18n routing. Not wired into the shipping
app; this is a standalone `npm create astro` project for evaluation only.

## What changed structurally

- **Content**: 3 typed YAML files (`src/content/domain/medical.{en,es,fr}.yaml`),
  auto-extracted from the existing `data-t-*` attributes so no re-translation was needed.
  Zod schema in `src/content.config.ts` — a missing/malformed field is now a **build
  error**, not a silent runtime gap.
- **Rendering**: one `DomainLayout.astro` component, three thin pages
  (`src/pages/{en,es,fr}/domain-medical.astro`) that just fetch the matching collection
  entry. `astro.config.mjs` sets `i18n.locales` / `prefixDefaultLocale: true`.
- **Output**: `astro build` emits fully static, pre-rendered HTML per locale
  (`dist/en/domain-medical.html`, `dist/es/...`, `dist/fr/...`) — verified by build + a
  direct read of the ES output. `<html lang="es">` is correct by construction; there's no
  `data-t-*` attribute or translation-toggle JS anywhere in the shipped HTML.

## Direct comparison to the current pattern

| | Current (`guide-ui.js` + `data-t-*`) | Astro pilot |
|---|---|---|
| Missing translation for a locale | Silently falls back to English at runtime | Zod schema error at build time |
| Adding a 4th language | Add a `data-t-xx` attribute to every element, everywhere | Add one YAML file |
| Client JS shipped for translation | Yes, `guide-ui.js` on every page | None — the right language is already the file that shipped |
| "Selected language shows English anyway" class of bug | Possible if wiring is missed (this is exactly what triggered this work) | Not structurally possible — each locale is a separate static file |
| Editing prose without touching markup | No — text lives inline in HTML attributes | Yes — translators can edit YAML without touching the layout |

## Cost / effort to actually adopt this

- Adds a real build step (Node + `astro build`) ahead of Capacitor/Xcode bundling and
  GitHub Pages publish — currently `Parlance/web/` and `docs/` are plain static files
  copied by hand/CI with no compilation.
- Every one of the ~10 guide/dialect/domain pages would need the same
  HTML-attribute-soup → structured-YAML extraction this pilot did for one page. Content
  pages with heavy free-form prose (`guide-es.html`, `guide-fr.html` deep tips) fit less
  cleanly into a strict schema than this vocab/rules page did.
- The interactive pages (journal, dialect region-picker JS) aren't content-collection
  candidates as-is; they'd stay hand-written `.astro` with client islands, so this doesn't
  replace `journal.js`.
- Parent-app integration changes: today the app opens one guide URL and toggles language
  client-side via `postMessage`; with this model the app would instead pick
  `/{lang}/domain-medical.html` up front, which is a small but real change to
  `journal.js`'s `openGuideOverlay`.

## Recommendation

The pilot confirms Astro's i18n routing + content collections *does* solve the exact bug
class that started this thread (selected language not applying inside guide content),
and does it by construction rather than by discipline/guard-scripts. It's a good fit
specifically for the **content pages** (`domain-*`, `dialect-*`, and eventually
`guide-*`), not for the interactive journal.

Given the current guard scripts (`check_guide_i18n.py`, `check_i18n.py` in CI) already
catch the recurring failure mode for near-zero ongoing cost, and a full migration is
multi-page effort plus a new build step in the release pipeline, this is a **worthwhile
follow-on project, not an urgent one**. Suggested next step if greenlit: migrate the
`domain-medical.html` / `domain-legal.html` pair for real (they're small, already
trilingual, and have the least free-form prose), then decide whether to continue into
`dialect-*` and `guide-*` based on how that goes.
