// ── AI PROVIDER CONFIGURATION ────────────────────────────────────
const AI_PROVIDERS = {
  webllm: {
    id: 'webllm',
    name: 'Browser AI',
    subtitle: 'Free · No account · On-device',
    icon: '🧠',
    requiresKey: false,
    local: true,
    corsNote: false,
    models: [
      { id: 'Qwen2.5-0.5B-Instruct-q4f16_1-MLC', name: 'Qwen 0.5B — Fast (~380 MB)' },
      { id: 'Qwen2.5-1.5B-Instruct-q4f16_1-MLC', name: 'Qwen 1.5B — Better (~900 MB)' },
    ],
    defaultModel: 'Qwen2.5-0.5B-Instruct-q4f16_1-MLC',
  },
  groq: {
    id: 'groq',
    name: 'Groq',
    subtitle: 'Free · Very fast',
    icon: '⚡',
    requiresKey: true,
    local: false,
    corsNote: false,
    free: true,
    endpoint: 'https://api.groq.com/openai/v1/chat/completions',
    keyUrl: 'https://console.groq.com/keys',
    models: [
      { id: 'qwen/qwen3-32b', name: 'Qwen3 32B (multilingual)' },
      { id: 'openai/gpt-oss-120b', name: 'GPT-OSS 120B (best)' },
      { id: 'meta-llama/llama-4-scout-17b-16e-instruct', name: 'Llama 4 Scout (fast)' },
    ],
    defaultModel: 'qwen/qwen3-32b',
  },
  deepseek: {
    id: 'deepseek',
    name: 'DeepSeek',
    subtitle: 'Free · DeepSeek V4',
    icon: '🐋',
    requiresKey: true,
    local: false,
    corsNote: false,
    free: true,
    endpoint: 'https://api.deepseek.com/chat/completions',
    keyUrl: 'https://platform.deepseek.com/api_keys',
    models: [
      { id: 'deepseek-v4-flash', name: 'DeepSeek V4 Flash (fast)' },
      { id: 'deepseek-v4-pro', name: 'DeepSeek V4 Pro (best)' },
    ],
    defaultModel: 'deepseek-v4-flash',
  },
  gemini: {
    id: 'gemini',
    name: 'Gemini',
    subtitle: 'Free · 1M tokens/day',
    icon: '✨',
    requiresKey: true,
    local: false,
    corsNote: false,
    free: true,
    keyUrl: 'https://aistudio.google.com/app/apikey',
    models: [
      { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash (stable)' },
      { id: 'gemini-3-flash-preview', name: 'Gemini 3 Flash (best)' },
    ],
    defaultModel: 'gemini-2.5-flash',
  },
  openrouter: {
    id: 'openrouter',
    name: 'OpenRouter',
    subtitle: 'Free models · Multi-provider',
    icon: '🔀',
    requiresKey: true,
    local: false,
    corsNote: false,
    free: true,
    endpoint: 'https://openrouter.ai/api/v1/chat/completions',
    keyUrl: 'https://openrouter.ai/keys',
    models: [
      { id: 'meta-llama/llama-3.3-70b-instruct:free', name: 'Llama 3.3 70B (free)' },
      { id: 'google/gemma-3-27b-it:free', name: 'Gemma 3 27B (free)' },
      { id: 'qwen/qwen3-8b:free', name: 'Qwen3 8B (free)' },
    ],
    defaultModel: 'meta-llama/llama-3.3-70b-instruct:free',
  },
  openai: {
    id: 'openai',
    name: 'OpenAI',
    subtitle: 'GPT-5 · Paid',
    icon: '💎',
    requiresKey: true,
    local: false,
    corsNote: false,
    free: false,
    endpoint: 'https://api.openai.com/v1/chat/completions',
    keyUrl: 'https://platform.openai.com/api-keys',
    models: [
      { id: 'gpt-5.4-nano', name: 'GPT-5.4 Nano (fast)' },
      { id: 'gpt-5.4-mini', name: 'GPT-5.4 Mini (best)' },
      { id: 'gpt-5.5', name: 'GPT-5.5 (premium)' },
    ],
    defaultModel: 'gpt-5.4-nano',
  },
  anthropic: {
    id: 'anthropic',
    name: 'Anthropic',
    subtitle: 'Claude · Paid',
    icon: '🤖',
    requiresKey: true,
    local: false,
    corsNote: true,
    free: false,
    keyUrl: 'https://console.anthropic.com/settings/keys',
    models: [
      { id: 'claude-haiku-4-5', name: 'Claude Haiku 4.5 (fast)' },
      { id: 'claude-sonnet-4-6', name: 'Claude Sonnet 4.6 (best)' },
      { id: 'claude-opus-4-7', name: 'Claude Opus 4.7 (premium)' },
    ],
    defaultModel: 'claude-haiku-4-5',
  },
  kimi: {
    id: 'kimi',
    name: 'Kimi',
    subtitle: 'Kimi K2.6 · Paid',
    icon: '🌙',
    requiresKey: true,
    local: false,
    corsNote: true,
    free: false,
    endpoint: 'https://api.moonshot.cn/v1/chat/completions',
    keyUrl: 'https://platform.moonshot.cn/console/api-keys',
    models: [
      { id: 'kimi-k2.5', name: 'Kimi K2.5 (multimodal)' },
      { id: 'kimi-k2.6', name: 'Kimi K2.6 (best)' },
    ],
    defaultModel: 'kimi-k2.6',
  },
};

// ── AI SETTINGS (localStorage) ───────────────────────────────────
const LS_PROVIDER = 'parlance_ai_provider';
const LS_MODEL    = 'parlance_ai_model_';
const LS_KEY      = 'parlance_ai_key_';

function getSelectedProvider() {
  return localStorage.getItem(LS_PROVIDER) || 'webllm';
}

function getProviderModel(providerId) {
  return localStorage.getItem(LS_MODEL + providerId) || AI_PROVIDERS[providerId]?.defaultModel || '';
}

function getProviderKey(providerId) {
  return localStorage.getItem(LS_KEY + providerId) || '';
}

function setSelectedProvider(id) { localStorage.setItem(LS_PROVIDER, id); }
function setProviderModel(id, m)  { localStorage.setItem(LS_MODEL + id, m); }
function setProviderKey(id, k)    { localStorage.setItem(LS_KEY + id, k); }

// ── WEBLLM ENGINE ────────────────────────────────────────────────
let webLLMEngine = null;
let webLLMLoadingPromise = null;
let webLLMCurrentModelId = null;

async function ensureWebLLM(modelId, progressCallback) {
  if (webLLMEngine && webLLMCurrentModelId === modelId) return webLLMEngine;

  if (webLLMLoadingPromise) {
    // Already loading — attach progress UI but share the same promise
    return webLLMLoadingPromise;
  }

  webLLMEngine = null;

  if (!navigator.gpu) {
    throw new Error(
      'WebGPU is not available in your browser. Please use Chrome 113+ or Edge 113+, ' +
      'or switch to a cloud provider in ⚙ AI settings.'
    );
  }

  webLLMLoadingPromise = (async () => {
    try {
      const webllm = await import('https://esm.run/@mlc-ai/web-llm');
      const engine = await webllm.CreateMLCEngine(modelId, {
        initProgressCallback: (report) => {
          if (progressCallback) progressCallback(report);
        },
      });
      webLLMEngine = engine;
      webLLMCurrentModelId = modelId;
      return engine;
    } finally {
      webLLMLoadingPromise = null;
    }
  })();

  return webLLMLoadingPromise;
}

// ── SYSTEM PROMPT BUILDER ─────────────────────────────────────────
function buildSystemPrompt(langName, level, ragContext) {
  const registerLabel = langName === 'French' ? 'tu/vous' : 'tú/usted';

  let nextLevel, targetLevel, levelGuidance;

  switch (level.toUpperCase()) {
    case 'C2':
      nextLevel = 'native-polish';
      targetLevel = null;
      levelGuidance = `Focus on near-native precision, stylistic elegance, idiomatic naturalness, and \
register mastery for professional interpreting. Flag any residual Anglicisms, calques, or unnatural phrasing. \
Provide a next_level_alt showing the most polished native-level phrasing. \
Identify the register used (${registerLabel}, formal/informal) and whether it is appropriate.`;
      break;
    case 'C1':
      nextLevel = 'C2';
      targetLevel = null;
      levelGuidance = `Focus on professional register, advanced word precision, and naturalness for interpreting. \
Flag Anglicisms (English sentence structures used in ${langName}). \
Provide a next_level_alt showing C2 native-mastery phrasing. \
Identify the register (${registerLabel}) and whether it matches a professional interpreting context.`;
      break;
    case 'B2':
      nextLevel = 'C1';
      targetLevel = 'C2';
      levelGuidance = `Focus on verb tense correctness (especially subjunctive vs indicative), gender/number agreement, \
and Anglicisms. Identify the register: is the sentence formal or informal? Would an interpreter use this phrasing \
in a professional setting? Explain ${registerLabel} choice. \
Provide next_level_alt (C1 professional interpreter phrasing) and target_level_alt (C2 native mastery).`;
      break;
    case 'B1':
      nextLevel = 'B2';
      targetLevel = 'C1';
      levelGuidance = `Focus on basic verb tense correctness and gender agreement. Be encouraging and clear. \
Identify the register: is the learner using ${registerLabel} appropriately? \
Introduce the concept of formal vs informal register for interpreter training. \
Provide next_level_alt (B2 with more complex structures) and target_level_alt (C1 professional interpreter phrasing).`;
      break;
    case 'A2':
      nextLevel = 'B1';
      targetLevel = 'B2';
      levelGuidance = `Focus on basic present tense conjugation, gender agreement, and simple sentence structure. \
Be encouraging. Check reflexive verbs, near future constructions, and basic vocabulary. \
Gently introduce register awareness: note whether the sentence uses ${registerLabel} and explain why it matters \
for someone training to become an interpreter. \
Provide next_level_alt (B1 with past tenses) and target_level_alt (B2 complexity).`;
      break;
    default: // A1
      nextLevel = 'A2';
      targetLevel = 'B1';
      levelGuidance = `Focus on basic present tense, fundamental verb usage, and simple vocabulary. \
Be very encouraging — this is an absolute beginner training to become an interpreter. \
Check subject-verb agreement and basic word order. Gently note register: is the learner using ${registerLabel}? \
Explain the difference simply and why interpreters must know both forms. \
Provide next_level_alt (A2 with slightly more complex structures) and target_level_alt (B1 phrasing).`;
  }

  const targetLine = targetLevel
    ? `"target_level_alt": "Same idea at ${targetLevel} level in ${langName}"`
    : '"target_level_alt": null';

  let prompt = `You are a ${langName} professor training professional interpreters. The learner is at CEFR level ${level}.

${levelGuidance}

`;

  if (ragContext) {
    prompt += `REFERENCE KNOWLEDGE (use these rules to verify accuracy):
${ragContext}

`;
  }

  prompt += `CRITICAL ACCURACY RULES:
- Do NOT invent grammatical errors. Only flag real, clear mistakes.
- A simple, grammatically correct sentence is "Excellent" even if it could be more sophisticated.
- Only mark "Needs Improvement" when there is an actual grammar error — not just a style preference.
- ALL example sentences (correction, next_level_alt, target_level_alt) MUST be written in ${langName}, NEVER in English.
- grammar_rule, explanation, register, and tip must be in English.

Respond with ONLY a valid JSON object. No markdown fences, no text outside the JSON, no <think> tags:
{
  "status": "Excellent" or "Needs Improvement",
  "grammar_rule": "The specific grammar rule tested or applied — always explain, even when correct",
  "explanation": "WHY the sentence is correct or incorrect at the ${level} level — be specific and actionable",
  "correction": null or "Corrected sentence in ${langName} (only if Needs Improvement)",
  "register": "Identify the register: formal (${langName === 'French' ? 'vous' : 'usted'}) or informal (${langName === 'French' ? 'tu' : 'tú'}), and whether appropriate for a professional interpreter",
  "next_level_alt": "Same idea at ${nextLevel} level in ${langName}",
  ${targetLine},
  "tip": "A practical tip about register, Anglicisms, or word precision for interpreter training"
}`;

  return prompt;
}

// ── API CALL: OpenAI-compatible format ────────────────────────────
// Works for: Groq, OpenAI, Kimi
async function callOpenAIFormat(endpoint, model, apiKey, systemPrompt, userMessage) {
  const resp = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userMessage },
      ],
      temperature: 0.3,
      max_tokens: 1024,
      response_format: { type: 'json_object' },
    }),
  });

  if (!resp.ok) {
    const body = await resp.text().catch(() => '');
    throw new Error(`${resp.status} from API: ${body.slice(0, 200)}`);
  }

  const data = await resp.json();
  return data.choices?.[0]?.message?.content ?? '';
}

// ── API CALL: Anthropic Messages API ─────────────────────────────
async function callAnthropic(model, apiKey, systemPrompt, userMessage) {
  const resp = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'anthropic-dangerous-direct-browser-access': 'true',
    },
    body: JSON.stringify({
      model,
      max_tokens: 1024,
      system: systemPrompt,
      messages: [{ role: 'user', content: userMessage }],
    }),
  });

  if (!resp.ok) {
    const body = await resp.text().catch(() => '');
    throw new Error(`Anthropic ${resp.status}: ${body.slice(0, 200)}`);
  }

  const data = await resp.json();
  return data.content?.[0]?.text ?? '';
}

// ── API CALL: Gemini generateContent API ─────────────────────────
async function callGemini(model, apiKey, systemPrompt, userMessage) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      system_instruction: { parts: [{ text: systemPrompt }] },
      contents: [{ parts: [{ text: userMessage }] }],
      generationConfig: {
        temperature: 0.3,
        maxOutputTokens: 1024,
        responseMimeType: 'application/json',
      },
    }),
  });

  if (!resp.ok) {
    const body = await resp.text().catch(() => '');
    throw new Error(`Gemini ${resp.status}: ${body.slice(0, 200)}`);
  }

  const data = await resp.json();
  return data.candidates?.[0]?.content?.parts?.[0]?.text ?? '';
}

// ── API CALL: WebLLM (local) ─────────────────────────────────────
async function callWebLLM(engine, systemPrompt, userMessage) {
  const reply = await engine.chat.completions.create({
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userMessage },
    ],
    temperature: 0.3,
    max_tokens: 1024,
  });
  return reply.choices?.[0]?.message?.content ?? '';
}

// ── JSON PARSE & NORMALIZE ────────────────────────────────────────
function parseAIContent(raw) {
  const cleaned = (raw || '')
    .replace(/<think>[\s\S]*?<\/think>/gi, '')
    .replace(/```json\s*/gi, '')
    .replace(/```\s*/g, '')
    .trim();

  // Find the first JSON object in the response
  const start = cleaned.indexOf('{');
  const end = cleaned.lastIndexOf('}');
  if (start === -1 || end === -1) throw new Error('No JSON object found in response');

  const jsonStr = cleaned.slice(start, end + 1);
  return JSON.parse(jsonStr);
}

function normalizeResult(raw) {
  const result = {};
  result.status      = (raw.status === 'Excellent' || raw.status === 'Needs Improvement')
    ? raw.status : 'Excellent';
  result.grammar_rule = raw.grammar_rule || raw.grammarRule || 'Grammar rule not identified';
  result.explanation  = raw.explanation  || '';
  if (raw.correction)       result.correction      = raw.correction;
  if (raw.register)         result.register        = raw.register;
  if (raw.next_level_alt)   result.next_level_alt  = raw.next_level_alt;
  if (raw.target_level_alt) result.target_level_alt = raw.target_level_alt;
  if (raw.tip)              result.tip             = raw.tip;
  return result;
}

// ── UNIFIED ANALYSIS ─────────────────────────────────────────────
// Called by analyzeSentence() — routes to the selected provider
async function analyzeWithAI(sentence, language, level, progressCallback) {
  // Check offline cache first
  try {
    const cacheKey = 'parlance_analysis_cache';
    const cache = JSON.parse(localStorage.getItem(cacheKey) || '{}');
    const hash = btoa(unescape(encodeURIComponent(
      sentence + '|' + language + '|' + level
    ))).slice(0, 40);
    if (cache[hash]) {
      return { ...cache[hash].feedback, _cachedSource: (cache[hash].source || 'cached') + ' (cached)' };
    }
  } catch (_) {}

  const providerId = getSelectedProvider();
  const provider   = AI_PROVIDERS[providerId];
  if (!provider) throw new Error('Unknown AI provider');

  const ragContext  = typeof getRAGContext === 'function'
    ? getRAGContext(language, level, sentence) : '';
  const langName    = language === 'fr' ? 'French' : 'Spanish';
  const systemPrompt = buildSystemPrompt(langName, level, ragContext);
  const userMessage  = `Analyze this ${langName} sentence at ${level} level: "${sentence}"`;

  // Wrap in a 20-second timeout for cloud providers
  const timeoutMs = providerId === 'webllm' ? 120000 : 20000;
  const timeoutPromise = new Promise((_, reject) =>
    setTimeout(() => reject(new Error(`${provider.name} timed out. Check your connection or try another provider in ⚙ AI.`)), timeoutMs)
  );

  const analysisPromise = (async () => {
    let rawContent;

    if (providerId === 'webllm') {
      if (!navigator.gpu) {
        throw new Error('Your browser does not support WebGPU (needed for Browser AI). Switch to a cloud provider like Groq (free) in ⚙ AI settings.');
      }
      const modelId = getProviderModel('webllm');
      const engine  = await ensureWebLLM(modelId, progressCallback);
      rawContent    = await callWebLLM(engine, systemPrompt, userMessage);

    } else if (providerId === 'anthropic') {
      const key   = getProviderKey('anthropic');
      if (!key) throw new Error('No Anthropic API key. Add one in ⚙ AI settings.');
      rawContent  = await callAnthropic(getProviderModel('anthropic'), key, systemPrompt, userMessage);

    } else if (providerId === 'gemini') {
      const key   = getProviderKey('gemini');
      if (!key) throw new Error('No Gemini API key. Add one in ⚙ AI settings.');
      rawContent  = await callGemini(getProviderModel('gemini'), key, systemPrompt, userMessage);

    } else {
      // OpenAI-compatible: groq, openai, kimi
      const key   = getProviderKey(providerId);
      if (!key) throw new Error(`No ${provider.name} API key. Add one in ⚙ AI settings.`);
      rawContent  = await callOpenAIFormat(
        provider.endpoint, getProviderModel(providerId), key, systemPrompt, userMessage
      );
    }

    return rawContent;
  })();

  const rawContent = await Promise.race([analysisPromise, timeoutPromise]);
  const parsed = parseAIContent(rawContent);
  const result = normalizeResult(parsed);

  // Cache the analysis result in localStorage
  try {
    const cacheKey = 'parlance_analysis_cache';
    const cache = JSON.parse(localStorage.getItem(cacheKey) || '{}');
    const hash = btoa(unescape(encodeURIComponent(
      sentence + '|' + language + '|' + level
    ))).slice(0, 40);
    cache[hash] = { feedback: result, source: AI_PROVIDERS[providerId]?.name || providerId, ts: Date.now() };
    // Keep cache to 200 entries max
    const keys = Object.keys(cache);
    if (keys.length > 200) {
      const sorted = keys.sort((a, b) => cache[a].ts - cache[b].ts);
      sorted.slice(0, keys.length - 200).forEach(k => delete cache[k]);
    }
    localStorage.setItem(cacheKey, JSON.stringify(cache));
  } catch (_) {}

  return result;
}

// ── UI LANGUAGE (i18n) ───────────────────────────────────────────
const UI_LANGS = {
  en: { name: 'English' },
  es: { name: 'Español' },
  fr: { name: 'Français' },
};

const UI_STRINGS = {
  en: {
    appTitle: 'Parlance',
    entryTitlePlaceholder: 'Entry title…',
    sentenceCount: (n) => `${n} sentence${n !== 1 ? 's' : ''}`,
    wordCount: (n) => `${n} word${n !== 1 ? 's' : ''}`,
    addSentence: 'Add another sentence',
    saveEntry: 'Save Entry',
    feedback: 'Feedback',
    prompts: 'Prompts',
    guide: 'Guide',
    waitingText: 'Write a sentence and pause.<br><br>AI feedback appears here automatically.',
    promptLabel: 'Click a prompt to use it as your first sentence',
    pastEntries: 'Past Entries',
    analyzing: 'Analyzing your sentence…',
    delete: 'Delete',
    loadAll: 'Load All to Editor',
    reAnalyze: 'Re-analyze',
    entrySaved: 'Entry saved!',
    entryDeleted: 'Entry deleted.',
    entryLoaded: 'Entry loaded into editor.',
    writeFirst: 'Write at least one sentence first.',
    privacy: 'Privacy',
    offline: "You're offline — writing is saved locally, but cloud AI feedback requires a connection.",
  },
  es: {
    appTitle: 'Parlance',
    entryTitlePlaceholder: 'Título de la entrada…',
    sentenceCount: (n) => `${n} oración${n !== 1 ? 'es' : ''}`,
    wordCount: (n) => `${n} palabra${n !== 1 ? 's' : ''}`,
    addSentence: 'Agregar otra oración',
    saveEntry: 'Guardar entrada',
    feedback: 'Retroalimentación',
    prompts: 'Ideas',
    guide: 'Guía',
    waitingText: 'Escribe una oración y pausa.<br><br>La retroalimentación aparecerá aquí automáticamente.',
    promptLabel: 'Haz clic en una idea para usarla como tu primera oración',
    pastEntries: 'Entradas anteriores',
    analyzing: 'Analizando tu oración…',
    delete: 'Eliminar',
    loadAll: 'Cargar todo al editor',
    reAnalyze: 'Re-analizar',
    entrySaved: '¡Entrada guardada!',
    entryDeleted: 'Entrada eliminada.',
    entryLoaded: 'Entrada cargada en el editor.',
    writeFirst: 'Escribe al menos una oración primero.',
    privacy: 'Privacidad',
    offline: 'Estás sin conexión — lo escrito se guarda localmente, pero la IA en la nube requiere conexión.',
  },
  fr: {
    appTitle: 'Parlance',
    entryTitlePlaceholder: "Titre de l'entrée…",
    sentenceCount: (n) => `${n} phrase${n !== 1 ? 's' : ''}`,
    wordCount: (n) => `${n} mot${n !== 1 ? 's' : ''}`,
    addSentence: 'Ajouter une phrase',
    saveEntry: "Sauvegarder l'entrée",
    feedback: 'Retour',
    prompts: 'Idées',
    guide: 'Guide',
    waitingText: 'Écrivez une phrase et faites une pause.<br><br>Le retour apparaîtra ici automatiquement.',
    promptLabel: 'Cliquez sur une idée pour commencer',
    pastEntries: 'Entrées précédentes',
    analyzing: 'Analyse de votre phrase…',
    delete: 'Supprimer',
    loadAll: "Tout charger dans l'éditeur",
    reAnalyze: 'Ré-analyser',
    entrySaved: 'Entrée sauvegardée !',
    entryDeleted: 'Entrée supprimée.',
    entryLoaded: "Entrée chargée dans l'éditeur.",
    writeFirst: "Écrivez au moins une phrase d'abord.",
    privacy: 'Confidentialité',
    offline: 'Vous êtes hors ligne — vos écrits sont sauvegardés localement, mais le retour IA nécessite une connexion.',
  },
};

function getUILang() {
  return localStorage.getItem('parlance_ui_lang') || 'en';
}

function setUILang(lang) {
  localStorage.setItem('parlance_ui_lang', lang);
}

function t(key) {
  const lang = getUILang();
  const strings = UI_STRINGS[lang] || UI_STRINGS.en;
  return strings[key] || UI_STRINGS.en[key] || key;
}

function onUILangChange() {
  const lang = document.getElementById('uiLangSelect').value;
  setUILang(lang);
  applyUILang();
}

function applyUILang() {
  const lang = getUILang();
  document.getElementById('uiLangSelect').value = lang;

  // Update static UI text
  document.getElementById('entryTitle').placeholder = t('entryTitlePlaceholder');
  document.querySelector('.add-sentence-btn').innerHTML = '<span>+</span> ' + t('addSentence');
  document.querySelector('.save-btn').textContent = t('saveEntry');

  // Tabs
  const tabs = document.querySelectorAll('.feedback-tab');
  if (tabs[0]) tabs[0].textContent = t('feedback');
  if (tabs[1]) tabs[1].textContent = t('prompts');
  if (tabs[2]) tabs[2].textContent = t('guide');

  // Waiting text
  const waitingText = document.getElementById('waitingText');
  if (waitingText) waitingText.innerHTML = t('waitingText');

  // Prompt label
  const promptLabel = document.querySelector('.prompt-label');
  if (promptLabel) promptLabel.textContent = t('promptLabel');

  // Past entries title
  const pastTitle = document.querySelector('.past-bar-title');
  if (pastTitle) pastTitle.textContent = t('pastEntries');

  // Offline banner
  const offlineBanner = document.getElementById('offlineBanner');
  if (offlineBanner) offlineBanner.textContent = t('offline');

  // Privacy button
  const privacyBtn = document.querySelector('.privacy-link:not(.ai-settings-btn):not([onclick*="openAISettings"])');
  if (privacyBtn && !privacyBtn.textContent.includes('AI')) privacyBtn.textContent = t('privacy');

  // Delete button in entry viewer
  const deleteBtn = document.getElementById('entryDeleteBtn');
  if (deleteBtn) deleteBtn.textContent = t('delete');

  // Update counts with correct language
  updateCounts();
}

// ── DARK MODE ────────────────────────────────────────────────────
function initTheme() {
  const saved = localStorage.getItem('parlance_theme');
  if (saved === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
  updateThemeIcon();
}

function toggleTheme() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  if (isDark) {
    document.documentElement.removeAttribute('data-theme');
    localStorage.setItem('parlance_theme', 'light');
  } else {
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('parlance_theme', 'dark');
  }
  updateThemeIcon();
  const guideFrame = document.getElementById('guideFrame');
  if (guideFrame?.contentDocument?.body) {
    guideFrame.contentDocument.body.classList.toggle('dark', !isDark);
  }
}

function updateThemeIcon() {
  const btn = document.getElementById('themeToggle');
  if (!btn) return;
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  btn.textContent = isDark ? '☾' : '☀';
}

// ── LANGUAGE DEFINITIONS ──────────────────────────────────────────
const languages = {
  es: {
    code: 'es',
    name: 'Español',
    placeholder: 'Escribe una oración en español…',
    titlePlaceholder: 'Entry title… (e.g. Mi primer día en Valencia)',
    coachRole: 'Spanish',
    guideFile: 'guide-es.html',
    prompts: [
      'Describe your first day learning Spanish.',
      'What does being an interpreter mean to you?',
      'Talk about a place you would like to visit in Spain or Latin America.',
      'Describe an important person in your life.',
      'What are your professional goals for this year?',
      'Write about a cultural tradition you find interesting.',
      'What do you think about the importance of languages in today\'s world?',
    ],
  },
  fr: {
    code: 'fr',
    name: 'Français',
    placeholder: 'Écrivez une phrase en français…',
    titlePlaceholder: 'Entry title… (e.g. Mon premier jour à Paris)',
    coachRole: 'French',
    guideFile: 'guide-fr.html',
    prompts: [
      'Describe your first day learning French.',
      'What does being an interpreter mean to you?',
      'Talk about a place you would like to visit in France or Francophone Africa.',
      'Describe an important person in your life.',
      'What are your professional goals for this year?',
      'Write about a cultural tradition you find interesting.',
      'What do you think about the importance of languages in today\'s world?',
    ],
  },
};

// ── STATE ─────────────────────────────────────────────────────────
const state = {
  sentences: [],
  activeSentenceId: null,
  debounceTimers: {},
  savedEntries: [],
  isOnline: navigator.onLine,
  currentLanguage: 'es',
};

// ── AI SETTINGS UI ────────────────────────────────────────────────
let modalSelectedProvider = 'webllm';

function openAISettings() {
  modalSelectedProvider = getSelectedProvider();
  renderProviderGrid();
  updateModalForProvider(modalSelectedProvider);
  document.getElementById('aiSettingsOverlay').style.display = 'flex';
}

function closeAISettings() {
  document.getElementById('aiSettingsOverlay').style.display = 'none';
}

function renderProviderGrid() {
  const grid = document.getElementById('providerGrid');
  grid.innerHTML = '';
  Object.values(AI_PROVIDERS).filter(p => p.id !== 'webllm' || canUseWebLLM).forEach(p => {
    const card = document.createElement('div');
    card.className = 'ai-provider-card' + (p.id === modalSelectedProvider ? ' selected' : '');
    card.dataset.id = p.id;
    card.innerHTML = `
      <div class="ai-provider-icon">${p.icon}</div>
      <div class="ai-provider-name">${p.name}</div>
      <div class="ai-provider-sub">${p.subtitle}</div>
    `;
    card.addEventListener('click', () => {
      modalSelectedProvider = p.id;
      grid.querySelectorAll('.ai-provider-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      updateModalForProvider(p.id);
    });
    grid.appendChild(card);
  });
}

function updateModalForProvider(id) {
  const provider = AI_PROVIDERS[id];

  // API key section
  const keySection  = document.getElementById('apiKeySection');
  const apiKeyInput = document.getElementById('apiKeyInput');
  const apiKeyHint  = document.getElementById('apiKeyHint');
  if (provider.requiresKey) {
    keySection.style.display = '';
    apiKeyInput.value = getProviderKey(id);
    apiKeyHint.innerHTML = provider.keyUrl
      ? `Get a free key at <a href="${provider.keyUrl}" target="_blank" rel="noopener" style="color:var(--accent)">${provider.keyUrl.replace('https://', '')}</a>`
      : '';
  } else {
    keySection.style.display = 'none';
    apiKeyInput.value = '';
    apiKeyHint.innerHTML = '';
  }

  // Model dropdown
  const modelSel = document.getElementById('modalModelSelect');
  modelSel.innerHTML = '';
  const savedModel = getProviderModel(id);
  provider.models.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m.id;
    opt.textContent = m.name;
    opt.selected = m.id === savedModel;
    modelSel.appendChild(opt);
  });

  // CORS warning
  document.getElementById('corsWarning').style.display = provider.corsNote ? '' : 'none';
}

function saveAISettingsFromModal() {
  const id    = modalSelectedProvider;
  const model = document.getElementById('modalModelSelect').value;
  const key   = document.getElementById('apiKeyInput').value.trim();

  setSelectedProvider(id);
  setProviderModel(id, model);
  if (AI_PROVIDERS[id]?.requiresKey && key) setProviderKey(id, key);

  // Reset engine if WebLLM model changed
  if (id === 'webllm' && webLLMCurrentModelId !== model) {
    webLLMEngine = null;
    webLLMCurrentModelId = null;
  }

  closeAISettings();
  updateWaitingCard();
  showToast(`AI provider set to ${AI_PROVIDERS[id].name}. ✓`);
}

// ── PLATFORM DETECTION ────────────────────────────────────────────
const isCapacitor = !!(window.Capacitor);
const isAndroid   = isCapacitor && window.Capacitor.getPlatform?.() === 'android';
const hasWebGPU   = !!navigator.gpu;
const canUseWebLLM = hasWebGPU && !isCapacitor;

// ── INIT ──────────────────────────────────────────────────────────
function init() {
  initTheme();
  const savedUILang = getUILang();
  document.getElementById('uiLangSelect').value = savedUILang;
  applyUILang();

  document.getElementById('dateBadge').textContent = new Date()
    .toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

  const savedLang = localStorage.getItem('parlance_language') || 'es';
  state.currentLanguage = savedLang;
  document.getElementById('langSelect').value = savedLang;

  // Auto-switch from WebLLM if it can't run (Android WebView, no WebGPU)
  const currentProvider = getSelectedProvider();
  if (currentProvider === 'webllm' && !canUseWebLLM) {
    const fallback = ['groq', 'openai', 'gemini', 'anthropic', 'kimi']
      .find(id => getProviderKey(id));
    if (fallback) {
      setSelectedProvider(fallback);
    }
  }

  updateWaitingCard();
  renderPrompts();
  addSentence();
  loadSavedEntries();
  initNetworkMonitor();
  updatePlaceholders();

  // On Android/Capacitor with no cloud provider configured, prompt AI settings
  if (!canUseWebLLM && getSelectedProvider() === 'webllm') {
    setTimeout(() => openAISettings(), 500);
  }
}

function updateWaitingCard() {
  const id   = getSelectedProvider();
  const p    = AI_PROVIDERS[id];
  const hint = document.getElementById('waitingProviderHint');
  const text = document.getElementById('waitingText');
  if (!hint || !p) return;

  if (id === 'webllm') {
    if (canUseWebLLM) {
      hint.innerHTML = `${p.icon} <strong>Browser AI</strong> — first use downloads ~380 MB (cached after). Or <button onclick="openAISettings()" style="background:none;border:none;color:var(--accent);font-family:inherit;font-size:inherit;cursor:pointer;padding:0;text-decoration:underline">switch to a cloud API</button> for instant feedback.`;
    } else {
      hint.innerHTML = `⚙ <button onclick="openAISettings()" style="background:none;border:none;color:var(--accent);font-family:inherit;font-size:inherit;cursor:pointer;padding:0;text-decoration:underline">Set up an AI provider</button> to get feedback. Groq is free — get a key at <a href="https://console.groq.com/keys" target="_blank" style="color:var(--accent)">console.groq.com</a>.`;
    }
  } else {
    const hasKey = !!getProviderKey(id);
    if (hasKey) {
      hint.textContent = `${p.icon} ${p.name} — write a sentence to get feedback.`;
    } else {
      hint.innerHTML = `⚙ <button onclick="openAISettings()" style="background:none;border:none;color:var(--accent);font-family:inherit;font-size:inherit;cursor:pointer;padding:0;text-decoration:underline">Add your ${p.name} API key</button> to enable feedback.`;
    }
  }
}

// ── LANGUAGE SWITCHING ────────────────────────────────────────────
function onLanguageChange() {
  state.currentLanguage = document.getElementById('langSelect').value;
  localStorage.setItem('parlance_language', state.currentLanguage);
  updatePlaceholders();
  renderPrompts();
  loadGuide();
}

function currentLang() {
  return languages[state.currentLanguage] || languages.es;
}

function updatePlaceholders() {
  const lang = currentLang();
  document.getElementById('entryTitle').placeholder = lang.titlePlaceholder;
  document.querySelectorAll('.sentence-input').forEach(ta => {
    if (!ta.value) ta.placeholder = lang.placeholder;
  });
}

// ── NETWORK MONITOR ───────────────────────────────────────────────
function initNetworkMonitor() {
  updateOnlineStatus(navigator.onLine);
  window.addEventListener('online',  () => updateOnlineStatus(true));
  window.addEventListener('offline', () => updateOnlineStatus(false));
}

function updateOnlineStatus(online) {
  state.isOnline = online;
  document.getElementById('offlineBanner').classList.toggle('show', !online);
}

// ── PRIVACY POLICY ────────────────────────────────────────────────
function showPrivacyPolicy() {
  document.getElementById('privacyOverlay').style.display = 'flex';
}

function closePrivacyPolicy() {
  document.getElementById('privacyOverlay').style.display = 'none';
}

// ── PROMPTS ───────────────────────────────────────────────────────
function renderPrompts() {
  const list = document.getElementById('promptList');
  list.innerHTML = '';
  currentLang().prompts.forEach(p => {
    const el = document.createElement('div');
    el.className = 'prompt-item';
    el.textContent = p;
    el.onclick = () => usePrompt(p);
    list.appendChild(el);
  });
}

function usePrompt(p) {
  const empty = state.sentences.find(s => !s.text.trim());
  if (empty) {
    const ta = document.getElementById('ta-' + empty.id);
    if (ta) { ta.value = p; ta.dispatchEvent(new Event('input')); ta.focus(); }
  } else {
    addSentence(p);
  }
  switchTab('feedback', document.querySelector('.feedback-tab'));
}

// ── SENTENCES ─────────────────────────────────────────────────────
let sentenceIdCounter = 0;

function addSentence(prefill = '') {
  const id       = ++sentenceIdCounter;
  const sentence = { id, text: '', feedback: null, status: 'empty' };
  state.sentences.push(sentence);

  const area = document.getElementById('sentencesArea');
  const row  = document.createElement('div');
  row.className = 'sentence-row';
  row.id = 'row-' + id;
  row.innerHTML = `
    <div class="sentence-num">${state.sentences.length}</div>
    <div class="sentence-input-wrap">
      <textarea
        class="sentence-input"
        id="ta-${id}"
        placeholder="${currentLang().placeholder}"
        rows="1"
        spellcheck="false"
      ></textarea>
      <div class="sentence-status" id="status-${id}"></div>
    </div>
  `;
  area.appendChild(row);

  const ta = row.querySelector('textarea');
  ta.addEventListener('input', () => onSentenceInput(id));
  ta.addEventListener('keydown', (e) => onSentenceKeydown(e, id));
  ta.addEventListener('focus', () => { state.activeSentenceId = id; showFeedback(id); });
  ta.addEventListener('input', () => {
    ta.style.height = 'auto';
    ta.style.height = ta.scrollHeight + 'px';
  });

  if (prefill) {
    ta.value = prefill;
    ta.dispatchEvent(new Event('input'));
  }

  updateCounts();
  setTimeout(() => ta.focus(), 50);
  return id;
}

function onSentenceInput(id) {
  const ta       = document.getElementById('ta-' + id);
  const text     = ta.value;
  const sentence = state.sentences.find(s => s.id === id);
  if (!sentence) return;
  sentence.text     = text;
  sentence.status   = 'dirty';
  sentence.feedback = null;
  updateCounts();

  clearTimeout(state.debounceTimers[id]);
  if (text.trim().length > 5) {
    showAnalyzingState(id);
    state.debounceTimers[id] = setTimeout(() => {
      if (sentence.text.trim()) analyzeSentence(id);
    }, 1500);
  }
}

function onSentenceKeydown(e, id) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    const ta   = document.getElementById('ta-' + id);
    const text = ta.value.trim();
    if (text) {
      clearTimeout(state.debounceTimers[id]);
      state.activeSentenceId = id;   // ensure panel updates for this sentence
      analyzeSentence(id);
    }
  }
}

function updateCounts() {
  const sentences = state.sentences.filter(s => s.text.trim());
  document.getElementById('sentenceCount').textContent =
    t('sentenceCount')(sentences.length);
  const words = sentences.reduce(
    (acc, s) => acc + s.text.trim().split(/\s+/).filter(Boolean).length, 0
  );
  document.getElementById('wordCount').textContent =
    t('wordCount')(words);

  state.sentences.forEach((s, i) => {
    const num = document.querySelector(`#row-${s.id} .sentence-num`);
    if (num) num.textContent = i + 1;
  });
}

// ── ANALYSIS ──────────────────────────────────────────────────────
async function analyzeSentence(id) {
  const sentence = state.sentences.find(s => s.id === id);
  if (!sentence || !sentence.text.trim()) return;

  const ta       = document.getElementById('ta-' + id);
  const statusEl = document.getElementById('status-' + id);
  ta.classList.add('analyzing');
  ta.classList.remove('has-error', 'is-great');
  statusEl.textContent = '⏳';

  const level = document.getElementById('levelSelect').value;

  showAnalyzingState(id);

  const providerId = getSelectedProvider();

  try {
    const result = await analyzeWithAI(
      sentence.text,
      state.currentLanguage,
      level,
      (report) => showWebLLMProgress(report)
    );

    if (result._cachedSource) {
      sentence.analysisSource = result._cachedSource;
      delete result._cachedSource;
    } else {
      sentence.analysisSource = AI_PROVIDERS[providerId]?.name || providerId;
    }
    applyFeedback(id, sentence, result, ta, statusEl);

  } catch (err) {
    ta.classList.remove('analyzing');
    statusEl.textContent = '';
    console.error('[Parlance] Analysis error:', err);

    const msg = err.message || 'Could not analyze — check your settings.';
    showErrorInPanel(msg);
    showToast(msg.length > 80 ? msg.slice(0, 80) + '…' : msg);
  }
}

function applyFeedback(id, sentence, parsed, ta, statusEl) {
  sentence.feedback = parsed;
  sentence.status   = parsed.status === 'Excellent' ? 'great' : 'error';
  ta.classList.remove('analyzing');
  ta.classList.toggle('is-great', sentence.status === 'great');
  ta.classList.toggle('has-error', sentence.status === 'error');
  statusEl.textContent = sentence.status === 'great' ? '✓' : '⚠';
  if (state.activeSentenceId === id) showFeedback(id);
}

// ── FEEDBACK DISPLAY ──────────────────────────────────────────────
function switchTab(tab, btn) {
  if (tab === 'guide') { openGuideOverlay(); return; }
  document.querySelectorAll('.feedback-tab').forEach(t => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
  document.getElementById('feedbackInner').style.display  = tab === 'feedback' ? 'flex' : 'none';
  document.getElementById('promptsInner').style.display   = tab === 'prompts'  ? 'flex' : 'none';
  document.getElementById('guideInner').style.display     = 'none';
}

function clearFeedbackCards() {
  const inner = document.getElementById('feedbackInner');
  const waiting = document.getElementById('waitingCard');
  if (waiting) waiting.style.display = 'none';
  inner.querySelectorAll('.feedback-card, .analyzing-card, .webllm-progress-card, .error-panel-card').forEach(el => el.remove());
}

function showAnalyzingState(id) {
  clearFeedbackCards();
  const inner = document.getElementById('feedbackInner');
  const card  = document.createElement('div');
  card.className = 'analyzing-card';
  card.id = 'analyzing-card';
  card.innerHTML = `
    <div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
    <div class="analyzing-text">${t('analyzing')}</div>
  `;
  inner.appendChild(card);
}

function showWebLLMProgress(report) {
  const inner   = document.getElementById('feedbackInner');
  let card      = inner.querySelector('.webllm-progress-card');
  const pct     = Math.round((report.progress || 0) * 100);
  const text    = report.text || 'Loading model…';

  if (!card) {
    clearFeedbackCards();
    card = document.createElement('div');
    card.className = 'webllm-progress-card';
    card.innerHTML = `
      <div class="webllm-progress-title">🧠 Loading Browser AI</div>
      <div class="webllm-progress-text" id="webllmProgressText">${text}</div>
      <div class="webllm-progress-bar-wrap">
        <div class="webllm-progress-fill" id="webllmProgressFill" style="width:${pct}%"></div>
      </div>
      <div class="webllm-progress-sub">First load only — cached in your browser after this.</div>
    `;
    inner.appendChild(card);
  } else {
    const textEl = card.querySelector('#webllmProgressText');
    const fillEl = card.querySelector('#webllmProgressFill');
    if (textEl) textEl.textContent = text;
    if (fillEl) fillEl.style.width = pct + '%';
  }
}

function showErrorInPanel(msg) {
  clearFeedbackCards();
  const inner = document.getElementById('feedbackInner');
  const card  = document.createElement('div');
  card.className = 'error-panel-card';
  card.innerHTML = `
    <div class="error-panel-icon">⚠</div>
    <div class="error-panel-msg">${escapeHTML(msg)}</div>
    <button class="error-panel-btn" onclick="openAISettings()">⚙ Open AI Settings</button>
  `;
  inner.appendChild(card);
}

function showFeedback(id) {
  const sentence = state.sentences.find(s => s.id === id);
  if (!sentence) return;

  const inner   = document.getElementById('feedbackInner');
  const waiting = document.getElementById('waitingCard');
  if (waiting) waiting.style.display = 'none';
  inner.querySelectorAll('.feedback-card, .analyzing-card, .webllm-progress-card, .error-panel-card').forEach(el => el.remove());

  if (!sentence.feedback) {
    if (sentence.status === 'dirty' || sentence.text.trim()) showAnalyzingState(id);
    else if (waiting) waiting.style.display = 'block';
    return;
  }

  const fb          = sentence.feedback;
  const isExcellent = fb.status === 'Excellent';
  const statusLabel = isExcellent ? 'Excellent' : 'Needs Work';
  const statusClass = isExcellent ? 'score-excellent' : 'score-needs-work';

  const level       = document.getElementById('levelSelect').value;
  const nextLabels   = { C2: 'Native Polish', C1: 'C2 Mastery', B2: 'C1 Professional', B1: 'B2 Version', A2: 'B1 Version', A1: 'A2 Version' };
  const targetLabels = { B2: 'C2 Mastery', B1: 'C1 Professional', A2: 'B2 Version', A1: 'B1 Version' };
  const nextLabel    = nextLabels[level]   || 'Next Level';
  const targetLabel  = targetLabels[level] || null;

  let body = '';
  body += feedbackItem('label-rule',         '📐 Grammar Rule',  fb.grammar_rule);
  body += feedbackItem(
    'label-explanation',
    isExcellent ? '✨ Why This Works' : '⚠ What Needs Work',
    fb.explanation
  );
  if (fb.correction)       body += feedbackItem('label-correction', '✍ Correction',             fb.correction);
  if (fb.register)         body += feedbackItem('label-register',   '🎭 Register',               fb.register);
  if (fb.next_level_alt)   body += feedbackItem('label-next',       `🔼 ${nextLabel} Version`,   fb.next_level_alt);
  if (fb.target_level_alt && targetLabel)
                           body += feedbackItem('label-target',     `🎯 ${targetLabel} Version`, fb.target_level_alt);
  if (fb.tip)              body += feedbackItem('label-tip',        '💡 Tip',                    fb.tip);

  const sourceLabel = sentence.analysisSource || 'AI';
  const idx         = state.sentences.findIndex(s => s.id === id) + 1;

  const card = document.createElement('div');
  card.className = 'feedback-card';
  card.innerHTML = `
    <div class="feedback-card-header">
      <div class="feedback-sentence-ref">Sentence ${idx}</div>
      <div class="feedback-score ${statusClass}">${statusLabel}</div>
      <div class="feedback-source">${escapeHTML(sourceLabel)}</div>
    </div>
    <div class="feedback-original">"${escapeHTML(sentence.text)}"</div>
    <div class="feedback-body">${body}</div>
  `;
  inner.appendChild(card);
  inner.scrollTop = 0;
}

function feedbackItem(labelClass, label, text) {
  return `
    <div class="feedback-item">
      <div class="feedback-item-label ${labelClass}">${label}</div>
      <div class="feedback-item-text">${escapeHTML(String(text || ''))}</div>
    </div>
  `;
}

// ── GUIDE OVERLAY ─────────────────────────────────────────────────
function loadGuide() {
  // Called on language switch — resets the guide overlay
  const frame = document.getElementById('guideFrame');
  if (frame && frame.src) frame.src = '';
}

function openGuideOverlay() {
  const lang    = currentLang();
  const overlay = document.getElementById('guideOverlay');
  const frame   = document.getElementById('guideFrame');

  if (!lang.guideFile) { showToast('Guide coming soon for this language.'); return; }

  frame.src = lang.guideFile;
  frame.onload = () => {
    const theme = document.documentElement.getAttribute('data-theme');
    if (theme === 'dark') {
      frame.contentDocument?.body?.classList.add('dark');
    }
  };
  overlay.style.display = 'block';
}

function closeGuideOverlay() {
  document.getElementById('guideOverlay').style.display = 'none';
  document.getElementById('guideFrame').src = '';
}

window.addEventListener('message', (e) => {
  if (e.data === 'closeGuide') closeGuideOverlay();
});

// ── SAVE / LOAD ───────────────────────────────────────────────────
function saveEntry() {
  const title     = document.getElementById('entryTitle').value || 'Untitled Entry';
  const sentences = state.sentences.filter(s => s.text.trim());
  if (!sentences.length) { showToast(t('writeFirst')); return; }

  const entry = {
    id:       Date.now(),
    title,
    language: state.currentLanguage,
    level:    document.getElementById('levelSelect').value,
    date:     new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    sentences: sentences.map(s => ({
      text: s.text,
      feedback: s.feedback || null,
      analysisSource: s.analysisSource || null,
    })),
  };

  state.savedEntries.unshift(entry);
  try { localStorage.setItem('parlance_entries', JSON.stringify(state.savedEntries)); } catch (_) {}

  renderPastEntries();
  showToast(t('entrySaved') + ' ✓');
}

function loadSavedEntries() {
  try {
    const saved = localStorage.getItem('parlance_entries');
    if (saved) { state.savedEntries = JSON.parse(saved); renderPastEntries(); }
  } catch (_) {}
}

function renderPastEntries() {
  if (!state.savedEntries.length) return;
  const bar  = document.getElementById('pastBar');
  const list = document.getElementById('pastEntries');
  bar.style.display = 'block';
  list.innerHTML = '';
  state.savedEntries.slice(0, 8).forEach(entry => {
    const chip = document.createElement('div');
    chip.className = 'past-entry-chip';
    const langLabel = entry.language ? ` [${entry.language.toUpperCase()}]` : '';
    chip.textContent = `${entry.date} — ${entry.title}${langLabel}`;
    chip.onclick = () => viewEntry(entry);
    list.appendChild(chip);
  });
}

// ── ENTRY VIEWER ──────────────────────────────────────────────────
function viewEntry(entry) {
  document.getElementById('entryViewerTitle').textContent = entry.title || 'Untitled Entry';
  const langName = entry.language === 'fr' ? 'Français' : 'Español';
  const levelLabel = entry.level ? ` · ${entry.level}` : '';
  document.getElementById('entryViewerMeta').textContent =
    `${entry.date} · ${langName}${levelLabel}`;

  const body = document.getElementById('entryViewerBody');
  body.innerHTML = '';

  // "Load All to Editor" button at the top
  const loadAllRow = document.createElement('div');
  loadAllRow.style.cssText = 'margin-bottom: 1rem; text-align: right;';
  const loadAllBtn = document.createElement('button');
  loadAllBtn.className = 'entry-load-btn';
  loadAllBtn.textContent = 'Load All to Editor';
  loadAllBtn.onclick = () => loadEntryToEditor(entry);
  loadAllRow.appendChild(loadAllBtn);
  body.appendChild(loadAllRow);

  (entry.sentences || []).forEach((s, i) => {
    // Backward compatibility: old entries stored sentences as plain strings
    const text = typeof s === 'string' ? s : s.text;
    const feedback = typeof s === 'string' ? null : s.feedback;
    const analysisSource = typeof s === 'string' ? null : s.analysisSource;

    const row = document.createElement('div');
    row.className = 'entry-viewer-sentence';

    let feedbackHTML = '';
    if (feedback) {
      const isExcellent = feedback.status === 'Excellent';
      const badgeClass = isExcellent ? 'excellent' : 'needs-work';
      const badgeLabel = isExcellent ? 'Excellent' : 'Needs Work';
      feedbackHTML = `
        <div class="entry-sentence-actions">
          <span class="entry-feedback-badge ${badgeClass}">${badgeLabel}</span>
          ${analysisSource ? `<span class="entry-feedback-badge" style="background:rgba(11,156,208,0.06);color:#0b9cd0;">${escapeHTML(analysisSource)}</span>` : ''}
        </div>
        ${feedback.grammar_rule ? `<div class="entry-feedback-rule">${escapeHTML(feedback.grammar_rule)}</div>` : ''}
        ${feedback.explanation ? `<div class="entry-feedback-rule" style="color:#5a534e;">${escapeHTML(feedback.explanation)}</div>` : ''}
      `;
    }

    row.innerHTML = `
      <div class="entry-viewer-num">${i + 1}</div>
      <div class="entry-viewer-text">
        ${escapeHTML(text)}
        ${feedbackHTML}
        <div class="entry-sentence-actions" style="margin-top:0.4rem;">
          <button class="entry-load-btn" data-index="${i}" title="Load this sentence into editor">Re-analyze</button>
        </div>
      </div>
    `;

    // Attach re-analyze click handler
    row.querySelector('.entry-load-btn[data-index]').addEventListener('click', () => {
      loadSentenceToEditor(text, entry.language, entry.level);
    });

    body.appendChild(row);
  });

  document.getElementById('entryDeleteBtn').onclick = () => deleteEntry(entry.id);

  const overlay = document.getElementById('entryOverlay');
  overlay.style.display = 'flex';
  overlay.onclick = (e) => { if (e.target === overlay) closeEntryViewer(); };
}

function loadSentenceToEditor(text, language, level) {
  // Set language and level if provided
  if (language) {
    state.currentLanguage = language;
    document.getElementById('langSelect').value = language;
    localStorage.setItem('parlance_language', language);
    updatePlaceholders();
    renderPrompts();
  }
  if (level) {
    document.getElementById('levelSelect').value = level;
  }

  // Find an empty sentence slot or add a new one
  const empty = state.sentences.find(s => !s.text.trim());
  if (empty) {
    const ta = document.getElementById('ta-' + empty.id);
    if (ta) { ta.value = text; ta.dispatchEvent(new Event('input')); ta.focus(); }
  } else {
    addSentence(text);
  }

  closeEntryViewer();
  switchTab('feedback', document.querySelector('.feedback-tab'));
}

function loadEntryToEditor(entry) {
  // Set language and level
  if (entry.language) {
    state.currentLanguage = entry.language;
    document.getElementById('langSelect').value = entry.language;
    localStorage.setItem('parlance_language', entry.language);
    updatePlaceholders();
    renderPrompts();
  }
  if (entry.level) {
    document.getElementById('levelSelect').value = entry.level;
  }

  // Set title
  if (entry.title) {
    document.getElementById('entryTitle').value = entry.title;
  }

  // Clear existing sentences from UI and state
  const area = document.getElementById('sentencesArea');
  area.innerHTML = '';
  state.sentences = [];
  sentenceIdCounter = 0;

  // Load each sentence from the entry
  (entry.sentences || []).forEach(s => {
    const text = typeof s === 'string' ? s : s.text;
    addSentence(text);
  });

  closeEntryViewer();
  switchTab('feedback', document.querySelector('.feedback-tab'));
  showToast(t('entryLoaded'));
}

function deleteEntry(entryId) {
  const idx = state.savedEntries.findIndex(e => e.id === entryId);
  if (idx === -1) return;
  state.savedEntries.splice(idx, 1);
  try { localStorage.setItem('parlance_entries', JSON.stringify(state.savedEntries)); } catch (_) {}
  closeEntryViewer();
  renderPastEntries();
  if (!state.savedEntries.length) document.getElementById('pastBar').style.display = 'none';
  showToast(t('entryDeleted'));
}

function closeEntryViewer() {
  document.getElementById('entryOverlay').style.display = 'none';
}

// ── UTILS ─────────────────────────────────────────────────────────
function showToast(msg) {
  const t = document.getElementById('errorToast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3500);
}

function escapeHTML(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── START ─────────────────────────────────────────────────────────
try {
  init();
} catch (err) {
  console.error('[Parlance] init failed:', err);
  const inner = document.getElementById('feedbackInner');
  if (inner) {
    inner.innerHTML = `<div style="padding:1.5rem;font-family:'DM Mono',monospace;font-size:0.78rem;color:#b44;border:1px solid #f0d;border-radius:4px;">
      ⚠ Parlance failed to start: ${err.message}<br><br>Try a hard refresh (Cmd+Shift+R).
    </div>`;
  }
}
