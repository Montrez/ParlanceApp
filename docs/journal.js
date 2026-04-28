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
    subtitle: 'Free tier · Very fast',
    icon: '⚡',
    requiresKey: true,
    local: false,
    corsNote: false,
    endpoint: 'https://api.groq.com/openai/v1/chat/completions',
    keyUrl: 'https://console.groq.com/keys',
    models: [
      { id: 'qwen/qwen3-32b', name: 'Qwen3 32B (best quality)' },
      { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B' },
      { id: 'llama-3.1-8b-instant', name: 'Llama 3.1 8B (fastest)' },
    ],
    defaultModel: 'qwen/qwen3-32b',
  },
  openai: {
    id: 'openai',
    name: 'OpenAI',
    subtitle: 'GPT-4o · Paid',
    icon: '💎',
    requiresKey: true,
    local: false,
    corsNote: false,
    endpoint: 'https://api.openai.com/v1/chat/completions',
    keyUrl: 'https://platform.openai.com/api-keys',
    models: [
      { id: 'gpt-4o-mini', name: 'GPT-4o Mini (fast, cheap)' },
      { id: 'gpt-4o', name: 'GPT-4o (best)' },
    ],
    defaultModel: 'gpt-4o-mini',
  },
  anthropic: {
    id: 'anthropic',
    name: 'Anthropic',
    subtitle: 'Claude · Paid',
    icon: '🤖',
    requiresKey: true,
    local: false,
    corsNote: true,
    keyUrl: 'https://console.anthropic.com/settings/keys',
    models: [
      { id: 'claude-3-5-haiku-latest', name: 'Claude 3.5 Haiku (fast)' },
      { id: 'claude-sonnet-4-5', name: 'Claude Sonnet 4.5 (best)' },
    ],
    defaultModel: 'claude-3-5-haiku-latest',
  },
  gemini: {
    id: 'gemini',
    name: 'Gemini',
    subtitle: 'Google · Free tier',
    icon: '✨',
    requiresKey: true,
    local: false,
    corsNote: false,
    keyUrl: 'https://aistudio.google.com/app/apikey',
    models: [
      { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash (fast)' },
      { id: 'gemini-2.5-flash-preview-04-17', name: 'Gemini 2.5 Flash (best)' },
    ],
    defaultModel: 'gemini-2.0-flash',
  },
  kimi: {
    id: 'kimi',
    name: 'Kimi',
    subtitle: 'Moonshot AI · Paid',
    icon: '🌙',
    requiresKey: true,
    local: false,
    corsNote: true,
    endpoint: 'https://api.moonshot.cn/v1/chat/completions',
    keyUrl: 'https://platform.moonshot.cn/console/api-keys',
    models: [
      { id: 'moonshot-v1-8k', name: 'Moonshot v1 8K' },
      { id: 'moonshot-v1-32k', name: 'Moonshot v1 32K' },
      { id: 'moonshot-v1-128k', name: 'Moonshot v1 128K' },
    ],
    defaultModel: 'moonshot-v1-8k',
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
  const providerId = getSelectedProvider();
  const provider   = AI_PROVIDERS[providerId];
  if (!provider) throw new Error('Unknown AI provider');

  const ragContext  = typeof getRAGContext === 'function'
    ? getRAGContext(language, level, sentence) : '';
  const langName    = language === 'fr' ? 'French' : 'Spanish';
  const systemPrompt = buildSystemPrompt(langName, level, ragContext);
  const userMessage  = `Analyze this ${langName} sentence at ${level} level: "${sentence}"`;

  let rawContent;

  if (providerId === 'webllm') {
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

  const parsed = parseAIContent(rawContent);
  return normalizeResult(parsed);
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
      'Describe cómo fue tu primer día aprendiendo español.',
      '¿Qué significa ser intérprete para ti?',
      'Habla sobre un lugar que te gustaría visitar en España o Latinoamérica.',
      'Describe a una persona importante en tu vida.',
      '¿Cuáles son tus metas profesionales para este año?',
      'Escribe sobre una tradición cultural que te parece interesante.',
      '¿Qué opinas sobre la importancia de los idiomas en el mundo actual?',
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
      "Décrivez votre premier jour d'apprentissage du français.",
      'Que signifie être interprète pour vous ?',
      'Parlez d'un endroit que vous aimeriez visiter en France ou en Afrique francophone.',
      'Décrivez une personne importante dans votre vie.',
      'Quels sont vos objectifs professionnels pour cette année ?',
      'Écrivez sur une tradition culturelle qui vous semble intéressante.',
      "Que pensez-vous de l'importance des langues dans le monde actuel ?",
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
  Object.values(AI_PROVIDERS).forEach(p => {
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

// ── INIT ──────────────────────────────────────────────────────────
function init() {
  document.getElementById('dateBadge').textContent = new Date()
    .toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

  const savedLang = localStorage.getItem('parlance_language') || 'es';
  state.currentLanguage = savedLang;
  document.getElementById('langSelect').value = savedLang;

  updateWaitingCard();
  renderPrompts();
  addSentence();
  loadSavedEntries();
  initNetworkMonitor();
  updatePlaceholders();
}

function updateWaitingCard() {
  const id   = getSelectedProvider();
  const p    = AI_PROVIDERS[id];
  const hint = document.getElementById('waitingProviderHint');
  const text = document.getElementById('waitingText');
  if (!hint || !p) return;

  if (id === 'webllm') {
    const hasGPU = !!navigator.gpu;
    if (hasGPU) {
      hint.innerHTML = `${p.icon} <strong>Browser AI</strong> — first use downloads ~380 MB (cached after). Or <button onclick="openAISettings()" style="background:none;border:none;color:var(--accent);font-family:inherit;font-size:inherit;cursor:pointer;padding:0;text-decoration:underline">switch to a cloud API</button> for instant feedback.`;
    } else {
      hint.innerHTML = `⚠ Your browser doesn't support WebGPU. <button onclick="openAISettings()" style="background:none;border:none;color:var(--accent);font-family:inherit;font-size:inherit;cursor:pointer;padding:0;text-decoration:underline">Choose a cloud provider</button> (Groq has a free tier).`;
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
    `${sentences.length} sentence${sentences.length !== 1 ? 's' : ''}`;
  const words = sentences.reduce(
    (acc, s) => acc + s.text.trim().split(/\s+/).filter(Boolean).length, 0
  );
  document.getElementById('wordCount').textContent =
    `${words} word${words !== 1 ? 's' : ''}`;

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

    sentence.analysisSource = AI_PROVIDERS[providerId]?.name || providerId;
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
    <div class="analyzing-text">Analyzing your sentence…</div>
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
  if (!sentences.length) { showToast('Write at least one sentence first.'); return; }

  const entry = {
    id:       Date.now(),
    title,
    language: state.currentLanguage,
    date:     new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    sentences: sentences.map(s => s.text),
  };

  state.savedEntries.unshift(entry);
  try { localStorage.setItem('parlance_entries', JSON.stringify(state.savedEntries)); } catch (_) {}

  renderPastEntries();
  showToast('Entry saved! ✓');
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
  document.getElementById('entryViewerMeta').textContent =
    `${entry.date} · ${langName}`;

  const body = document.getElementById('entryViewerBody');
  body.innerHTML = '';
  (entry.sentences || []).forEach((text, i) => {
    const row = document.createElement('div');
    row.className = 'entry-viewer-sentence';
    row.innerHTML = `
      <div class="entry-viewer-num">${i + 1}</div>
      <div class="entry-viewer-text">${escapeHTML(text)}</div>
    `;
    body.appendChild(row);
  });

  document.getElementById('entryDeleteBtn').onclick = () => deleteEntry(entry.id);

  const overlay = document.getElementById('entryOverlay');
  overlay.style.display = 'flex';
  overlay.onclick = (e) => { if (e.target === overlay) closeEntryViewer(); };
}

function deleteEntry(entryId) {
  const idx = state.savedEntries.findIndex(e => e.id === entryId);
  if (idx === -1) return;
  state.savedEntries.splice(idx, 1);
  try { localStorage.setItem('parlance_entries', JSON.stringify(state.savedEntries)); } catch (_) {}
  closeEntryViewer();
  renderPastEntries();
  if (!state.savedEntries.length) document.getElementById('pastBar').style.display = 'none';
  showToast('Entry deleted.');
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
