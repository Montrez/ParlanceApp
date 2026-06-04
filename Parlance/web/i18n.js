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
      waitingText: "Write a sentence, then press <strong>Enter</strong>.<br><br>Parlance infers your CEFR level and shows feedback here.",
      assessedLevelLabel: "Sentence level",
      assessedLevelText: "This sentence is at approximately {level} level.",
      assessedLevelRichText: "Inferred around {level} on the CEFR scale — the grammar and vocabulary in this sentence fit that band.",
      assessedLevelHint: "Inferred CEFR level for this sentence",
      complexityNoteLabel: "Sentence complexity",
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
      privacyUpdated: "Last updated: May 2026",
      prompts_es_1: "Describe your first day learning Spanish.",
      prompts_es_2: "What does being an interpreter mean to you?",
      prompts_es_3: "Talk about a place you would like to visit in Spain or Latin America.",
      prompts_es_4: "Describe an important person in your life.",
      prompts_es_5: "What are your professional goals for this year?",
      prompts_es_6: "Write about a cultural tradition you find interesting.",
      prompts_es_7: "What do you think about the importance of languages in today's world?",
      prompts_fr_1: "Describe your first day learning French.",
      prompts_fr_2: "What does being an interpreter mean to you?",
      prompts_fr_3: "Talk about a place you would like to visit in France or a Francophone country.",
      prompts_fr_4: "Describe an important person in your life.",
      prompts_fr_5: "What are your professional goals for this year?",
      prompts_fr_6: "Write about a French cultural tradition you find interesting.",
      prompts_fr_7: "What do you think about the importance of languages in today's world?"
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
      waitingText: "Escribe una oración y pulsa <strong>Enter</strong>.<br><br>Parlance infiere tu nivel MCER y muestra la retroalimentación aquí.",
      assessedLevelLabel: "Nivel de la oración",
      assessedLevelText: "Esta oración está aproximadamente en nivel {level}.",
      assessedLevelRichText: "Aproximadamente nivel {level} en el MCER — la gramática y el vocabulario de esta oración encajan en esa banda.",
      assessedLevelHint: "Nivel MCER inferido para esta oración",
      complexityNoteLabel: "Complejidad de la oración",
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
      privacyUpdated: "Última actualización: mayo 2026",
      prompts_es_1: "Describe tu primer día aprendiendo español.",
      prompts_es_2: "¿Qué significa ser intérprete para ti?",
      prompts_es_3: "Habla sobre un lugar que te gustaría visitar en España o Latinoamérica.",
      prompts_es_4: "Describe a una persona importante en tu vida.",
      prompts_es_5: "¿Cuáles son tus metas profesionales para este año?",
      prompts_es_6: "Escribe sobre una tradición cultural que te parezca interesante.",
      prompts_es_7: "¿Qué opinas sobre la importancia de los idiomas en el mundo actual?",
      prompts_fr_1: "Describe tu primer día aprendiendo francés.",
      prompts_fr_2: "¿Qué significa ser intérprete para ti?",
      prompts_fr_3: "Habla sobre un lugar que te gustaría visitar en Francia o un país francófono.",
      prompts_fr_4: "Describe a una persona importante en tu vida.",
      prompts_fr_5: "¿Cuáles son tus metas profesionales para este año?",
      prompts_fr_6: "Escribe sobre una tradición cultural francesa que te parezca interesante.",
      prompts_fr_7: "¿Qué opinas sobre la importancia de los idiomas en el mundo actual?"
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
      waitingText: "Écrivez une phrase, puis appuyez sur <strong>Entrée</strong>.<br><br>Parlance infère votre niveau CECR et affiche le retour ici.",
      assessedLevelLabel: "Niveau de la phrase",
      assessedLevelText: "Cette phrase est d'environ le niveau {level}.",
      assessedLevelRichText: "Environ le niveau {level} sur l'échelle CECR — la grammaire et le vocabulaire de cette phrase correspondent à cette bande.",
      assessedLevelHint: "Niveau CECR inféré pour cette phrase",
      complexityNoteLabel: "Complexité de la phrase",
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
      privacyUpdated: "Dernière mise à jour : mai 2026",
      prompts_es_1: "Décrivez votre premier jour d'apprentissage de l'espagnol.",
      prompts_es_2: "Que signifie être interprète pour vous ?",
      prompts_es_3: "Parlez d'un endroit que vous aimeriez visiter en Espagne ou en Amérique latine.",
      prompts_es_4: "Décrivez une personne importante dans votre vie.",
      prompts_es_5: "Quels sont vos objectifs professionnels pour cette année ?",
      prompts_es_6: "Écrivez sur une tradition culturelle que vous trouvez intéressante.",
      prompts_es_7: "Que pensez-vous de l'importance des langues dans le monde actuel ?",
      prompts_fr_1: "Décrivez votre premier jour d'apprentissage du français.",
      prompts_fr_2: "Que signifie être interprète pour vous ?",
      prompts_fr_3: "Parlez d'un endroit que vous aimeriez visiter en France ou dans un pays francophone.",
      prompts_fr_4: "Décrivez une personne importante dans votre vie.",
      prompts_fr_5: "Quels sont vos objectifs professionnels pour cette année ?",
      prompts_fr_6: "Écrivez sur une tradition culturelle française que vous trouvez intéressante.",
      prompts_fr_7: "Que pensez-vous de l'importance des langues dans le monde actuel ?"
    }
  }
};
