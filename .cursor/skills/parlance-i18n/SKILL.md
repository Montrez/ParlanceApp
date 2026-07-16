---
name: parlance-i18n
description: >-
  Keep Parlance interface language complete across locales, HTML, JS, dialect
  guides, docs/, and Xcode. Use whenever adding or changing user-visible text,
  buttons, toasts, placeholders, settings copy, waiting hints, guide chrome,
  UI language switching, i18n, localization, locales/*.json, data-i18n,
  data-t-en, guide-ui.js, or when the user reports text that stays English
  after changing app language.
---

# Parlance interface language (i18n)

**Never half-update.** If a string is user-visible, it must change when the
app language changes. Patching one English literal in HTML/JS without the
full pipeline is how the UX stays broken.

Practice language (what the user writes: ES/FR) ≠ interface language
(EN/ES/FR menus). This skill is **interface language only**.

## Single sources of truth

| Surface | Source | Apply mechanism |
|---|---|---|
| Journal, settings, toasts, waiting hints | `Parlance/web/locales/{en,es,fr}.json` | `data-i18n` / `data-i18n-html` / `data-i18n-placeholder` / `data-i18n-title` or `i18n.t('key')` |
| Offline fallback | `i18n.js` `_embedded` | **Generated** — never hand-edit |
| Dialect bilingual body/chrome | One DOM node with `data-t-en` + `data-t-native` (or `-html`) | `guide-ui.js` fills on language change |
| GitHub Pages | `docs/` | Must stay byte-identical to `Parlance/web/` for shared assets |
| Xcode bundle | `project.pbxproj` | New web files via `scripts/xcode_add_web_resources.py` |

## Mandatory checklist (every UI-string change)

Copy and complete; do not stop early:

```
i18n progress:
- [ ] Key added to locales/en.json AND es.json AND fr.json (same keys)
- [ ] Wired with data-i18n* OR i18n.t('key') — no leftover English literal in that path
- [ ] Dynamic UI (buttons created in JS, waiting card, open guide iframe) refreshes via i18n.onChange / refreshDynamicI18nUI — not only on first paint
- [ ] python3 scripts/sync_i18n_embedded.py
- [ ] python3 scripts/check_i18n.py  (must exit 0)
- [ ] Mirrored changed files into docs/
- [ ] If new .js/.html under Parlance/web/: python3 scripts/xcode_add_web_resources.py <file>
```

### Commands

```bash
# After editing locales/*.json
python3 scripts/sync_i18n_embedded.py
python3 scripts/check_i18n.py

# Mirror (example — sync every file you touched)
cp Parlance/web/locales/*.json docs/locales/
cp Parlance/web/i18n.js docs/i18n.js
# …and any other edited Parlance/web/* twin under docs/
```

## How to add a string

1. Add the same key to **all three** locale JSON files with proper translations.
2. Prefer declarative HTML:
   ```html
   <button data-i18n="saveAndClose">Save &amp; Close</button>
   <input data-i18n-placeholder="apiKeyPlaceholder" />
   <div data-i18n-html="waitingText"></div>
   ```
3. For JS-only / runtime strings:
   ```js
   showToast(i18n.t('providerSet', { name }));
   hint.innerHTML = i18n.t('waitingCloudReady', { icon, name });
   ```
4. Run sync + check + docs mirror (checklist above).

**Do not** leave English as the only copy in `journal.js` / `index.html` “for now.”
**Do not** edit `_embedded` by hand.
**Do not** update only `en.json`.

## Language change must refresh everything

`i18n.load(lang)` already calls `apply()` (all `data-i18n*`) and `_notify()`.

Anything **not** marked with `data-i18n*` must be refreshed from an
`i18n.onChange` listener (today: `refreshDynamicI18nUI` in `journal.js`):

- `.analyze-btn` labels
- waiting-card provider hints (`updateWaitingCard`)
- counts, prompts, date badge
- open dialect/guide iframe via `parlanceGuideEnv` postMessage

If you add a new dynamically created control, either:

- give it `data-i18n` / `data-i18n-title` when inserted into the DOM, **or**
- update it inside `refreshDynamicI18nUI`.

## Dialect / guide bilingual pages

**Forbidden:** twin siblings `.ui-en` + `.ui-native` with CSS hide/show.

**Required:** one element:

```html
<h1 data-t-en="Regional Guide" data-t-native="Dialectos">Regional Guide</h1>
<div data-t-en-html="<strong>Tip</strong> …" data-t-native-html="…"></div>
```

```html
<script src="guide-ui.js"></script>
<script>
GuideUI.init({
  nativeLang: 'es',  // or 'fr'
  storageKey: 'parlance_guide_read_es',
  titleEn: 'Regional Guide — Spanish',
  titleNative: 'Guía de dialectos — Español',
  onApplied: function () { if (typeof updatePair === 'function') updatePair(); }
});
</script>
```

Converting leftover twin markup:

```bash
python3 scripts/convert_dialect_bilingual.py
```

Parent journal must keep passing `?ui=` / `?theme=` and posting
`{ type: 'parlanceGuideEnv', ui, theme }` when UI language or theme changes.

## Adding a new UI language (e.g. German menus)

1. Copy `locales/en.json` → `locales/de.json` and translate values (same keys).
2. Add `<option value="de">` to `#uiLangSelect` in `index.html` (+ docs).
3. `sync_i18n_embedded.py` + `check_i18n.py`.
4. Mirror locales + i18n.js into `docs/`.
5. Register new locale file with Xcode if needed (`xcode_add_web_resources.py`).

Practice languages (new writing language) use `ADDING_A_LANGUAGE.md` /
`new_language_scaffold.py` — different system.

## Anti-patterns (reject these in review)

- Updating one locale file only
- Hardcoding toast/button copy in `journal.js` while locales already have a key
- Dual HTML for EN/native on dialect pages
- Editing `docs/` without `Parlance/web/` (or the reverse)
- Hand-editing `i18n.js` `_embedded`
- Fixing “Feedback stays English” by changing the HTML default text without a locale key + `data-i18n`
- Shipping without `check_i18n.py` exit 0

## Related docs

- Dev overview: `ADDING_A_LANGUAGE.md` → section **Interface language (i18n)**
- Scripts: `scripts/check_i18n.py`, `scripts/sync_i18n_embedded.py`, `scripts/convert_dialect_bilingual.py`
