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
        if (this._embedded[lang]) {
          this.messages[lang] = this._embedded[lang];
        } else {
          console.warn(`i18n: could not load locale "${lang}"`);
          return;
        }
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
  },

  _embedded: {
    en: {
      appTitle: "Parlance",
      entryTitlePlaceholder: "Entry title…",
      sentenceCount_one: "{n} sentence",
      sentenceCount_other: "{n} sentences",
      wordCount_one: "{n} word",
      wordCount_other: "{n} words",
      addSentence: "Add another sentence",
      saveEntry: "Save Entry",
      feedback: "Feedback",
      prompts: "Prompts",
      guide: "Guide",
      waitingText: "Write a sentence and pause.<br><br>AI feedback appears here automatically.",
      promptLabel: "Writing ideas — respond to one in your target language",
      pastEntries: "Past Entries",
      analyzing: "Analyzing your sentence…",
      delete: "Delete",
      loadAll: "Load All to Editor",
      reAnalyze: "Re-analyze",
      entrySaved: "Entry saved!",
      entryDeleted: "Entry deleted.",
      entryLoaded: "Entry loaded into editor.",
      writeFirst: "Write at least one sentence first.",
      privacy: "Privacy",
      offline: "You’re offline — writing is saved locally, but cloud AI feedback requires a connection.",
      privacyTitle: "Privacy Policy",
      privacyWritingTitle: "Your Writing",
      privacyWritingText: "Journal entries are stored only in your browser’s local storage and never sent to Parlance servers. You can delete any entry at any time.",
      privacyAITitle: "AI Analysis",
      privacyAIText1: "When you use Browser AI (WebLLM), your sentences are analyzed entirely on your device using a local model. No data leaves your browser.",
      privacyAIText2: "When you use a cloud provider (Groq, OpenAI, Anthropic, Gemini, or Kimi), each sentence you submit is sent to that provider’s API. Please review the privacy policy of your chosen provider.",
      privacyKeysTitle: "API Keys",
      privacyKeysText: "API keys you enter are stored in your browser’s local storage and are sent only to the respective provider’s API endpoint. Parlance never sees or stores your API keys.",
      privacyTrackingTitle: "No Tracking",
      privacyTrackingText: "Parlance does not use analytics, cookies, or any form of tracking. Nothing about your usage is collected or shared.",
      privacyUpdated: "Last updated: May 2026"
    },
    es: {
      appTitle: "Parlance",
      entryTitlePlaceholder: "Título de la entrada…",
      sentenceCount_one: "{n} oración",
      sentenceCount_other: "{n} oraciones",
      wordCount_one: "{n} palabra",
      wordCount_other: "{n} palabras",
      addSentence: "Agregar otra oración",
      saveEntry: "Guardar entrada",
      feedback: "Retroalimentación",
      prompts: "Ideas",
      guide: "Guía",
      waitingText: "Escribe una oración y pausa.<br><br>La retroalimentación aparecerá aquí automáticamente.",
      promptLabel: "Ideas para escribir — responde a una en tu idioma objetivo",
      pastEntries: "Entradas anteriores",
      analyzing: "Analizando tu oración…",
      delete: "Eliminar",
      loadAll: "Cargar todo al editor",
      reAnalyze: "Re-analizar",
      entrySaved: "¡Entrada guardada!",
      entryDeleted: "Entrada eliminada.",
      entryLoaded: "Entrada cargada en el editor.",
      writeFirst: "Escribe al menos una oración primero.",
      privacy: "Privacidad",
      offline: "Estás sin conexión — lo escrito se guarda localmente, pero la IA en la nube requiere conexión.",
      privacyTitle: "Política de privacidad",
      privacyWritingTitle: "Tu escritura",
      privacyWritingText: "Las entradas del diario se almacenan solo en el almacenamiento local de tu navegador y nunca se envían a los servidores de Parlance. Puedes eliminar cualquier entrada en cualquier momento.",
      privacyAITitle: "Análisis de IA",
      privacyAIText1: "Cuando usas Browser AI (WebLLM), tus oraciones se analizan completamente en tu dispositivo usando un modelo local. Ningún dato sale de tu navegador.",
      privacyAIText2: "Cuando usas un proveedor en la nube (Groq, OpenAI, Anthropic, Gemini o Kimi), cada oración que envías se envía a la API de ese proveedor. Revisa la política de privacidad de tu proveedor elegido.",
      privacyKeysTitle: "Claves API",
      privacyKeysText: "Las claves API que ingresas se almacenan en el almacenamiento local de tu navegador y solo se envían al punto de acceso API del proveedor respectivo. Parlance nunca ve ni almacena tus claves API.",
      privacyTrackingTitle: "Sin rastreo",
      privacyTrackingText: "Parlance no usa análisis, cookies ni ninguna forma de rastreo. Nada sobre tu uso se recopila ni se comparte.",
      privacyUpdated: "Última actualización: mayo 2026"
    },
    fr: {
      appTitle: "Parlance",
      entryTitlePlaceholder: "Titre de l’entrée…",
      sentenceCount_one: "{n} phrase",
      sentenceCount_other: "{n} phrases",
      wordCount_one: "{n} mot",
      wordCount_other: "{n} mots",
      addSentence: "Ajouter une phrase",
      saveEntry: "Sauvegarder l’entrée",
      feedback: "Retour",
      prompts: "Idées",
      guide: "Guide",
      waitingText: "Écrivez une phrase et faites une pause.<br><br>Le retour apparaîtra ici automatiquement.",
      promptLabel: "Idées d’écriture — répondez à une dans votre langue cible",
      pastEntries: "Entrées précédentes",
      analyzing: "Analyse de votre phrase…",
      delete: "Supprimer",
      loadAll: "Tout charger dans l’éditeur",
      reAnalyze: "Ré-analyser",
      entrySaved: "Entrée sauvegardée !",
      entryDeleted: "Entrée supprimée.",
      entryLoaded: "Entrée chargée dans l’éditeur.",
      writeFirst: "Écrivez au moins une phrase d’abord.",
      privacy: "Confidentialité",
      offline: "Vous êtes hors ligne — vos écrits sont sauvegardés localement, mais le retour IA nécessite une connexion.",
      privacyTitle: "Politique de confidentialité",
      privacyWritingTitle: "Vos écrits",
      privacyWritingText: "Les entrées du journal sont stockées uniquement dans le stockage local de votre navigateur et ne sont jamais envoyées aux serveurs de Parlance. Vous pouvez supprimer toute entrée à tout moment.",
      privacyAITitle: "Analyse IA",
      privacyAIText1: "Lorsque vous utilisez Browser AI (WebLLM), vos phrases sont analysées entièrement sur votre appareil à l’aide d’un modèle local. Aucune donnée ne quitte votre navigateur.",
      privacyAIText2: "Lorsque vous utilisez un fournisseur cloud (Groq, OpenAI, Anthropic, Gemini ou Kimi), chaque phrase soumise est envoyée à l’API de ce fournisseur. Veuillez consulter la politique de confidentialité du fournisseur choisi.",
      privacyKeysTitle: "Clés API",
      privacyKeysText: "Les clés API que vous saisissez sont stockées dans le stockage local de votre navigateur et envoyées uniquement au point d’accès API du fournisseur respectif. Parlance ne voit ni ne stocke jamais vos clés API.",
      privacyTrackingTitle: "Aucun suivi",
      privacyTrackingText: "Parlance n’utilise ni analyses, ni cookies, ni aucune forme de suivi. Rien concernant votre utilisation n’est collecté ni partagé.",
      privacyUpdated: "Dernière mise à jour : mai 2026"
    }
  }
};
