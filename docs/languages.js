// ── PRACTICE LANGUAGE REGISTRY ─────────────────────────────────────
// Single source of truth for Parlance's practice languages, shared by journal.js,
// rag-knowledge.js, and the coach-standard-*/coach-rules-* files. To add a language,
// add a row here (plus its content: guide/dialect HTML, coach standard/rules JS,
// locale strings) rather than adding new `=== 'es'` / `=== 'fr'` checks elsewhere.
//
// Loaded before rag-knowledge.js and journal.js — keep this a plain global (no ES
// module syntax) since the app loads scripts as classic <script> tags, including
// from a native WKWebView over file://.
const PARLANCE_LANGUAGES = {
  es: {
    code: 'es',
    name: 'Español',
    placeholder: 'Escribe un párrafo en español…',
    titlePlaceholder: 'Entry title… (e.g. Mi primer día en Valencia)',
    coachRole: 'Spanish',
    guideFile: 'guide-es.html',
    dialectFile: 'dialect-es.html',
    examKey: 'dele',
    hasOnDeviceModel: true,
    // Global set by coach-standard-es.js, read by ParlanceCoachStandard.forLang().
    coachStandardGlobal: 'ParlanceCoachStandardES',
  },
  fr: {
    code: 'fr',
    name: 'Français',
    placeholder: 'Écrivez un paragraphe en français…',
    titlePlaceholder: 'Entry title… (e.g. Mon premier jour à Paris)',
    coachRole: 'French',
    guideFile: 'guide-fr.html',
    dialectFile: 'dialect-fr.html',
    examKey: 'delf',
    hasOnDeviceModel: true,
    coachStandardGlobal: 'ParlanceCoachStandardFR',
  },

  en: {
    code: 'en',
    name: 'English',
    placeholder: 'Write a paragraph in English…',
    titlePlaceholder: 'Entry title… (e.g. My first day interpreting in English)',
    coachRole: 'English',
    guideFile: 'guide-en.html',
    dialectFile: 'dialect-en.html',
    examKey: 'toefl',
    hasOnDeviceModel: false,
    coachStandardGlobal: 'ParlanceCoachStandardEN',
  },
};

const PARLANCE_DEFAULT_LANGUAGE = 'es';

function parlanceLanguageInfo(code) {
  return PARLANCE_LANGUAGES[code] || PARLANCE_LANGUAGES[PARLANCE_DEFAULT_LANGUAGE];
}

// Startup assertion (issue #13 acceptance criteria): every registry entry must have a
// matching <option> in #langSelect, so a missing HTML option fails loudly in the console
// instead of silently making a language unselectable.
document.addEventListener('DOMContentLoaded', () => {
  const select = document.getElementById('langSelect');
  if (!select) return;
  const optionValues = Array.from(select.options).map(o => o.value);
  Object.keys(PARLANCE_LANGUAGES).forEach(code => {
    if (!optionValues.includes(code)) {
      console.error(`[languages.js] #langSelect is missing an <option value="${code}"> for a language defined in PARLANCE_LANGUAGES.`);
    }
  });
});
