const i18n = {
  locale: 'en',
  fallback: 'en',
  messages: {},

  async load(lang) {
    if (!this.messages[lang]) {
      try {
        const res = await fetch(`locales/${lang}.json`);
        this.messages[lang] = await res.json();
      } catch {
        console.warn(`i18n: could not load locale "${lang}"`);
        return;
      }
    }
    this.locale = lang;
    localStorage.setItem('parlance_ui_lang', lang);
    this.apply();
  },

  async init() {
    const saved = localStorage.getItem('parlance_ui_lang') || 'en';
    await this.load('en');
    if (saved !== 'en') await this.load(saved);
  },

  t(key, params) {
    const msg = this.messages[this.locale]?.[key]
             ?? this.messages[this.fallback]?.[key]
             ?? key;
    if (typeof msg !== 'string') return key;
    if (!params) return msg;
    return msg.replace(/\{(\w+)\}/g, (_, k) => params[k] ?? k);
  },

  tc(key, n) {
    const suffix = n === 1 ? '_one' : '_other';
    return this.t(key + suffix, { n });
  },

  apply() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      el.textContent = this.t(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
      el.innerHTML = this.t(el.dataset.i18nHtml);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      el.placeholder = this.t(el.dataset.i18nPlaceholder);
    });
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      el.title = this.t(el.dataset.i18nTitle);
    });
  },

  getLocale() {
    return this.locale;
  }
};
