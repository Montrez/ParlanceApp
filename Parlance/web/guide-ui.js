/**
 * Shared bilingual chrome for dialect (and future guide) pages.
 *
 * Markup uses one element per string:
 *   <h1 data-t-en="Regional Guide" data-t-native="Dialectos"></h1>
 *   <div data-t-en-html="<strong>Tip</strong> …" data-t-native-html="…"></div>
 *
 * Call GuideUI.init({ nativeLang, storageKey, titleEn, titleNative }) once per page.
 * Parent journal posts { type: 'parlanceGuideEnv', ui, theme } on language/theme change.
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

  function applyGuideEnv(cfg, ui, theme) {
    const useNative = ui === cfg.nativeLang;
    document.body.setAttribute('data-guide-ui', useNative ? 'native' : 'en');
    document.documentElement.lang = useNative ? cfg.nativeLang : 'en';
    if (theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
      document.body.classList.add('dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
      document.body.classList.remove('dark');
    }
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
    document.title = useNative ? cfg.titleNative : cfg.titleEn;
    if (typeof cfg.onApplied === 'function') cfg.onApplied(useNative);
  }

  const GuideUI = {
    /**
     * @param {{ nativeLang: string, storageKey: string, titleEn: string, titleNative: string, onApplied?: function }} cfg
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
