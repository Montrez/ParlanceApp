/**
 * Shared multilingual chrome for dialect and guide pages.
 *
 * Two modes, both driven by the app's interface language (`ui`), never the
 * practice language — the parent journal posts
 * { type: 'parlanceGuideEnv', ui, theme } whenever either changes, and this
 * re-applies live without reloading the iframe.
 *
 * 1. Binary (native-language content, e.g. dialect-es.html teaching Spanish
 *    dialects — the only two realistic UI languages for that audience are
 *    English or the target language itself):
 *      <h1 data-t-en="Regional Guide" data-t-native="Dialectos"></h1>
 *    GuideUI.init({ nativeLang: 'es', storageKey, titleEn, titleNative })
 *
 * 2. Multi (content pages whose audience's interface language can be any of
 *    en/es/fr regardless of what's being taught — e.g. guide-en.html /
 *    dialect-en.html, which teach English contrastively to ES *and* FR L1
 *    speakers, so a binary toggle can't cover both):
 *      <h1 data-t-en="English" data-t-es="Inglés" data-t-fr="Anglais"></h1>
 *    GuideUI.init({ langs: ['en','es','fr'], storageKey, titles: {en,es,fr} })
 *    Untranslated elements fall back to data-t-en.
 */
(function (global) {
  function applyBilingualTexts(useNative) {
    document.querySelectorAll('[data-t-en]').forEach((el) => {
      const en = el.getAttribute('data-t-en') ?? '';
      const native = el.getAttribute('data-t-native') ?? en;
      el.textContent = useNative ? native : en;
    });
    document.querySelectorAll('[data-t-en-html]').forEach((el) => {
      const en = el.getAttribute('data-t-en-html') ?? '';
      const native = el.getAttribute('data-t-native-html') ?? en;
      el.innerHTML = useNative ? native : en;
    });
    document.querySelectorAll('select option[data-en]').forEach((opt) => {
      const en = opt.getAttribute('data-en') || '';
      const native = opt.getAttribute('data-es')
        || opt.getAttribute('data-fr')
        || opt.getAttribute('data-native')
        || en;
      opt.textContent = useNative ? native : en;
    });
  }

  function applyMultilingualTexts(lang) {
    document.querySelectorAll('[data-t-en]').forEach((el) => {
      el.textContent = el.getAttribute('data-t-' + lang) ?? el.getAttribute('data-t-en') ?? '';
    });
    document.querySelectorAll('[data-t-en-html]').forEach((el) => {
      el.innerHTML = el.getAttribute('data-t-' + lang + '-html') ?? el.getAttribute('data-t-en-html') ?? '';
    });
    document.querySelectorAll('select option[data-en]').forEach((opt) => {
      opt.textContent = opt.getAttribute('data-' + lang) || opt.getAttribute('data-en') || '';
    });
  }

  function applyGuideEnv(cfg, ui, theme) {
    const isMulti = Array.isArray(cfg.langs);
    const lang = isMulti
      ? (cfg.langs.includes(ui) ? ui : 'en')
      : (ui === cfg.nativeLang ? cfg.nativeLang : 'en');
    const useNative = !isMulti && lang === cfg.nativeLang;

    document.body.setAttribute('data-guide-ui', isMulti ? lang : (useNative ? 'native' : 'en'));
    document.documentElement.lang = lang;
    if (theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
      document.body.classList.add('dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
      document.body.classList.remove('dark');
    }

    if (isMulti) {
      applyMultilingualTexts(lang);
    } else {
      applyBilingualTexts(useNative);
      document.querySelectorAll('.lang-switch a').forEach((a) => {
        try {
          const url = new URL(a.getAttribute('href'), location.href);
          url.searchParams.set('ui', useNative ? cfg.nativeLang : 'en');
          url.searchParams.set('theme', theme === 'dark' ? 'dark' : 'light');
          a.setAttribute('href', url.pathname.split('/').pop() + '?' + url.searchParams.toString());
        } catch (_) { /* ignore */ }
      });
      document.querySelectorAll('.guide-lang-btn').forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.guideRead === (useNative ? 'native' : 'en'));
      });
    }

    document.title = isMulti
      ? (cfg.titles && (cfg.titles[lang] || cfg.titles.en)) || document.title
      : (useNative ? cfg.titleNative : cfg.titleEn);
    if (typeof cfg.onApplied === 'function') cfg.onApplied(isMulti ? lang : useNative);
  }

  const GuideUI = {
    /**
     * @param {{ nativeLang?: string, langs?: string[], storageKey: string,
     *           titleEn?: string, titleNative?: string, titles?: Record<string,string>,
     *           onApplied?: function }} cfg
     */
    init(cfg) {
      global.applyGuideEnv = function (ui, theme) {
        applyGuideEnv(cfg, ui, theme);
      };
      global.setGuideReadLang = function (mode) {
        const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
        const ui = mode === 'native' ? cfg.nativeLang : 'en';
        applyGuideEnv(cfg, ui, theme);
        try { localStorage.setItem(cfg.storageKey, ui); } catch (_) {}
      };

      const params = new URLSearchParams(location.search);
      let ui = params.get('ui');
      if (!ui) {
        try { ui = localStorage.getItem(cfg.storageKey); } catch (_) {}
      }
      if (!ui) {
        try { ui = localStorage.getItem('parlance_ui_lang'); } catch (_) {}
      }
      applyGuideEnv(cfg, ui || 'en', params.get('theme') || 'light');
      global.addEventListener('message', (e) => {
        if (e.data && e.data.type === 'parlanceGuideEnv') {
          applyGuideEnv(cfg, e.data.ui || 'en', e.data.theme || 'light');
        }
      });
    },
  };

  global.GuideUI = GuideUI;
})(typeof window !== 'undefined' ? window : globalThis);
