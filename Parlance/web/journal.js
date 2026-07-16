// ── AI PROVIDER CONFIGURATION ────────────────────────────────────
const PARLANCE_SLM_URL = localStorage.getItem('parlance_slm_server_url') || 'http://127.0.0.1:8765';

/** Min trimmed length to analyze. */
const MIN_SENTENCE_CHARS = 15;
const MIN_SENTENCE_WORDS = 3;

/** Split a paragraph into sentence units for per-sentence feedback. */
function splitIntoSentences(text) {
  const trimmed = String(text || '').replace(/\s+/g, ' ').trim();
  if (!trimmed) return [];
  // Keep terminator with each unit. Handles . ! ? … and Spanish/French spacing.
  const parts = trimmed.match(/[^.!?…]+(?:[.!?…]+(?:\s*["»”']+)?|(?=$))/g);
  if (!parts) return [trimmed];
  return parts.map(p => p.trim()).filter(p => p.length > 0);
}

function countSentencesInText(text) {
  return splitIntoSentences(text).length;
}

/** Parlance Coach on-device first load can take 60–120s+ on iPhone. */
const TIMEOUT_MS = {
  parlanceNative: 300000,
  parlanceServer: 180000,
  webllm: 180000,
  cloud: 20000,
};

const VALID_CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

function normalizeAssessedLevel(raw) {
  if (!raw) return null;
  const u = String(raw).toUpperCase().trim();
  return VALID_CEFR_LEVELS.includes(u) ? u : null;
}

function extractAssessedLevel(obj) {
  if (!obj) return null;
  return normalizeAssessedLevel(obj.assessed_level || obj.assessedLevel || obj.sentence_level);
}

function extractComplexityNote(obj) {
  if (!obj) return null;
  const raw = obj.complexity_note || obj.complexityNote;
  if (!raw || typeof raw !== 'string') return null;
  const t = raw.trim();
  return t.length ? t : null;
}

function altVersionLabels(assessedLevel) {
  if (!assessedLevel) {
    return { nextLabel: 'Next Level', targetLabel: 'Higher Level' };
  }
  const nextLabels = {
    C2: 'Native Polish', C1: 'C2 Mastery', B2: 'C1 Professional',
    B1: 'B2 Version', A2: 'B1 Version', A1: 'A2 Version',
  };
  const targetLabels = {
    B2: 'C2 Mastery', B1: 'C1 Professional', A2: 'B2 Version', A1: 'B1 Version',
  };
  return {
    nextLabel: nextLabels[assessedLevel] || 'Next Level',
    targetLabel: targetLabels[assessedLevel] || null,
  };
}

function analysisCacheHash(sentence, language) {
  return btoa(unescape(encodeURIComponent(sentence + '|' + language + '|fbv13'))).slice(0, 40);
}

function sanitizeFeedbackResult(sentence, result, language = 'es') {
  if (typeof ParlanceFeedbackSanitize !== 'undefined' && ParlanceFeedbackSanitize.sanitizeFeedbackResult) {
    return ParlanceFeedbackSanitize.sanitizeFeedbackResult(sentence, result, language);
  }
  return result;
}

const AI_PROVIDERS = {
  parlance: {
    id: 'parlance',
    name: 'Parlance Coach',
    subtitle: 'Spanish & French fine-tuned · On-device',
    icon: '🎓',
    requiresKey: false,
    local: true,
    corsNote: false,
    models: [
      { id: 'parlance-es', name: 'Parlance Spanish (Qwen 0.5B)' },
      { id: 'parlance-fr', name: 'Parlance French (Qwen 0.5B)' },
    ],
    defaultModel: 'parlance-es',
  },
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

// ── FIREBASE AUTH & CLOUD PROXY ──────────────────────────────────
let firebaseApp = null;
let firebaseAuth = null;
let analyzeTextCallable = null;
let firebaseAuthUser = null;
let firebaseInitPromise = null;

const FIREBASE_PLACEHOLDER_API_KEY = 'YOUR_API_KEY';

function hasFirebaseConfig() {
  return typeof firebaseConfig !== 'undefined'
    && firebaseConfig?.apiKey
    && firebaseConfig.apiKey !== FIREBASE_PLACEHOLDER_API_KEY;
}

function isCloudProvider(providerId) {
  const p = AI_PROVIDERS[providerId];
  return !!(p && !p.local);
}

function isFirebaseSignedIn() {
  if (isNativeParlanceApp()) {
    return !!(window.__PARLANCE_AUTH__?.signedIn);
  }
  return !!firebaseAuthUser;
}

function firebaseDisplayName() {
  if (isNativeParlanceApp()) {
    const a = window.__PARLANCE_AUTH__ || {};
    return a.displayName || a.email || 'Signed in';
  }
  if (firebaseAuthUser) {
    return firebaseAuthUser.displayName || firebaseAuthUser.email || 'Signed in';
  }
  return '';
}

function shouldUseFirebaseCloud(providerId) {
  if (!isCloudProvider(providerId)) return false;
  return isFirebaseSignedIn();
}

function canUseFirebaseWebAuth() {
  return hasFirebaseConfig()
    && typeof firebase !== 'undefined'
    && !isNativeParlanceApp();
}

async function ensureFirebaseReady() {
  if (!canUseFirebaseWebAuth()) return false;
  if (firebaseApp && analyzeTextCallable) return true;
  if (firebaseInitPromise) return firebaseInitPromise;

  firebaseInitPromise = (async () => {
    try {
      if (!firebase.apps?.length) {
        firebaseApp = firebase.initializeApp(firebaseConfig);
      } else {
        firebaseApp = firebase.app();
      }
      firebaseAuth = firebase.auth();
      analyzeTextCallable = firebase.functions().httpsCallable('analyzeText');
      firebaseAuth.onAuthStateChanged((user) => {
        firebaseAuthUser = user;
        updateFirebaseAuthUI();
        updateModalForProvider(modalSelectedProvider);
        updateWaitingCard();
      });
      return true;
    } catch (e) {
      console.warn('[Parlance] Firebase init failed:', e);
      return false;
    } finally {
      firebaseInitPromise = null;
    }
  })();

  return firebaseInitPromise;
}

async function signInWithApple() {
  if (isNativeParlanceApp()) {
    try {
      await callNativeAuth('signInApple');
      showToast(i18n.t('signedInApple'));
    } catch (e) {
      const msg = e?.message || '';
      if (msg && msg !== 'cancelled' && !msg.includes('canceled')) {
        showToast(msg || i18n.t('appleSignInFailed'));
      }
    }
    updateFirebaseAuthUI();
    updateModalForProvider(modalSelectedProvider);
    updateWaitingCard();
    return;
  }
  if (!canUseFirebaseWebAuth()) return;
  await ensureFirebaseReady();
  const provider = new firebase.auth.OAuthProvider('apple.com');
  provider.addScope('email');
  provider.addScope('name');
  try {
    await firebaseAuth.signInWithPopup(provider);
    showToast(i18n.t('signedInApple'));
  } catch (e) {
    if (e?.code !== 'auth/popup-closed-by-user') {
      showToast(e?.message || i18n.t('appleSignInFailed'));
    }
  }
  updateFirebaseAuthUI();
}

async function signInWithGoogle() {
  if (isNativeParlanceApp()) {
    try {
      await callNativeAuth('signInGoogle');
      showToast(i18n.t('signedInGoogle'));
    } catch (e) {
      const msg = e?.message || '';
      if (msg && msg !== 'cancelled' && !msg.includes('canceled')) {
        showToast(msg || i18n.t('googleSignInFailed'));
      }
    }
    updateFirebaseAuthUI();
    updateModalForProvider(modalSelectedProvider);
    updateWaitingCard();
    return;
  }
  if (!canUseFirebaseWebAuth()) return;
  await ensureFirebaseReady();
  try {
    await firebaseAuth.signInWithPopup(new firebase.auth.GoogleAuthProvider());
    showToast(i18n.t('signedInGoogle'));
  } catch (e) {
    if (e?.code !== 'auth/popup-closed-by-user') {
      showToast(e?.message || i18n.t('googleSignInFailed'));
    }
  }
  updateFirebaseAuthUI();
}

async function signOutFirebase() {
  if (isNativeParlanceApp()) {
    try {
      await callNativeAuth('signOut');
      showToast(i18n.t('signedOut'));
    } catch (e) {
      showToast(e?.message || i18n.t('signOutFailed'));
    }
    updateFirebaseAuthUI();
    updateModalForProvider(modalSelectedProvider);
    updateWaitingCard();
    return;
  }
  if (canUseFirebaseWebAuth() && firebaseAuth) {
    try {
      await firebaseAuth.signOut();
    } catch (_) {}
  }
  updateFirebaseAuthUI();
  updateModalForProvider(modalSelectedProvider);
  updateWaitingCard();
  showToast(i18n.t('signedOut'));
}

function updateFirebaseAuthUI() {
  const section = document.getElementById('authSection');
  if (!section) return;

  const signedOut = document.getElementById('authSignedOut');
  const signedInEl = document.getElementById('authSignedIn');
  const authButtons = document.getElementById('authButtons');
  const authSetupHint = document.getElementById('authSetupHint');
  const native = isNativeParlanceApp();
  const webAuth = canUseFirebaseWebAuth();

  if (!hasFirebaseConfig() && !native) {
    section.style.display = 'none';
    return;
  }
  section.style.display = '';

  if (native) {
    if (authButtons) authButtons.style.display = '';
    if (authSetupHint) {
      authSetupHint.textContent =
        'Sign in with Apple or Google to use cloud AI without API keys.';
    }
  } else if (!webAuth) {
    section.style.display = 'none';
    return;
  } else {
    if (authButtons) authButtons.style.display = '';
    if (authSetupHint) {
      authSetupHint.textContent =
        'Sign in to use cloud AI without API keys (Groq, Gemini, …).';
    }
  }

  const signedIn = isFirebaseSignedIn();
  if (signedOut) signedOut.style.display = signedIn ? 'none' : '';
  if (signedInEl) signedInEl.style.display = signedIn ? '' : 'none';
  const label = document.getElementById('authUserLabel');
  if (label && signedIn) label.textContent = firebaseDisplayName();

  // Refresh usage counter when signed in
  if (signedIn) refreshUsageDisplay();
}

/** Fetch usage from Cloud Function and update the counter badge in the auth section. */
async function refreshUsageDisplay() {
  try {
    const ready = await ensureFirebaseReady();
    if (!ready) return;
    const fn = firebase.functions().httpsCallable('getUsage');
    const result = await fn({});
    const u = result.data;
    if (!u) return;

    const el = document.getElementById('authCloudNote');
    if (!el) return;

    if (u.tier === 'plus') {
      el.textContent = i18n.t('plusUnlimited');
      el.style.display = '';
      return;
    }

    const used = u.monthlyUsed || 0;
    const limit = u.monthlyLimit || 30;
    const packs = u.packCallsRemaining || 0;
    const remaining = Math.max(0, limit - used);

    let msg = `${remaining} free cloud calls left this month`;
    if (packs > 0) msg += ` · ${packs} pack calls remaining`;
    el.textContent = msg;
    el.style.display = '';
  } catch (_) {
    // Non-critical — silently skip if function unavailable
  }
}

function normalizeFirebaseAnalyzeResult(data, sentence, language = 'es') {
  if (!data) throw new Error('Empty response from cloud analysis');
  if (data.status === 'Excellent' || data.status === 'Needs Improvement') {
    return normalizeResult(data, sentence, language);
  }
  if (data.feedback && typeof data.feedback === 'object') {
    return normalizeResult(data.feedback, sentence, language);
  }
  const raw = data.rawContent ?? data.raw ?? (typeof data === 'string' ? data : null);
  if (raw) return normalizeResult(parseAIContent(raw), sentence, language);
  return normalizeResult(data, sentence, language);
}

function callNativeFirebaseAnalyze(sentence, language, providerId) {
  return new Promise((resolve, reject) => {
    if (!isNativeParlanceApp()) {
      reject(new Error('Native Firebase analysis is only available in the Parlance app.'));
      return;
    }
    const requestId = 'fb_' + Date.now() + '_' + Math.random().toString(36).slice(2);
    const timeoutId = setTimeout(() => {
      reject(new Error('Cloud AI via Parlance account timed out. Try again or switch provider in ⚙ AI.'));
    }, TIMEOUT_MS.cloud);
    const ragContext = typeof getRAGContext === 'function'
      ? getRAGContext(language, null, sentence) : '';
    window.__parlanceFirebaseResult = (id, result, err) => {
      if (id !== requestId) return;
      clearTimeout(timeoutId);
      delete window.__parlanceFirebaseResult;
      if (err) {
        reject(new Error(err));
        return;
      }
      try {
        if (typeof result === 'string') {
          resolve(normalizeFirebaseAnalyzeResult(parseAIContent(result), sentence, language));
        } else {
          resolve(normalizeFirebaseAnalyzeResult(result, sentence, language));
        }
      } catch (e) {
        reject(e);
      }
    };
    window.webkit.messageHandlers.parlance.postMessage({
      action: 'analyzeFirebase',
      requestId,
      sentence,
      language,
      ragContext,
      provider: providerId,
      model: getProviderModel(providerId),
    });
  });
}

async function callFirebaseCloudAnalyze(sentence, language, providerId) {
  if (isNativeParlanceApp() && window.__PARLANCE_AUTH__?.signedIn) {
    return callNativeFirebaseAnalyze(sentence, language, providerId);
  }
  const ready = await ensureFirebaseReady();
  if (!ready || !analyzeTextCallable) {
    throw new Error('Firebase is not configured.');
  }
  const ragContext = typeof getRAGContext === 'function'
    ? getRAGContext(language, null, sentence) : '';
  const resp = await analyzeTextCallable({
    sentence,
    language,
    ragContext,
    provider: providerId,
    model: getProviderModel(providerId),
  });
  return normalizeFirebaseAnalyzeResult(resp.data, sentence, language);
}

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
function buildSystemPrompt(langName, ragContext) {
  const registerLabel = langName === 'French' ? 'tu/vous' : 'tú/usted';
  const formalRegister = langName === 'French' ? 'vous' : 'usted';
  const informalRegister = langName === 'French' ? 'tu' : 'tú';
  const langKey = langName === 'French' ? 'fr' : 'es';
  const standardBlock = (typeof ParlanceCoachStandard !== 'undefined' && ParlanceCoachStandard.forLang)
    ? ParlanceCoachStandard.forLang(langKey)
    : '';

  let prompt = `You are a ${langName} professor training professional interpreters. Do NOT assume the learner picked a CEFR level.

Evaluate verb tense and mood, gender/number agreement, register (${registerLabel}), Anglicisms, and naturalness for professional interpreting.

`;
  if (standardBlock) {
    prompt += `${standardBlock}\n`;
  }

  prompt += `CEFR & COMPLEXITY:
- assessed_level: A1–C2 ONLY if highly confident from specific structures in this sentence. When uncertain, omit and use complexity_note without a CEFR label. Never guess from word count.
- complexity_note: 1–2 English sentences on vocabulary, syntax, subordination, and register — what makes this sentence simple or advanced. Always include when possible, even without assessed_level.
- next_level_alt / target_level_alt: stronger rewrites; CEFR labels only when assessed_level is set.

`;

  if (ragContext) {
    prompt += `REFERENCE KNOWLEDGE (use these rules to verify accuracy):
${ragContext}

`;
  }

  prompt += `CRITICAL ACCURACY RULES:
- Do NOT invent grammatical errors. Only flag real, clear mistakes.
- Grammatically correct sentences are "Excellent" — but explanation must cite specific structures in the learner's words (not generic praise).
- Only mark "Needs Improvement" when there is an actual grammar error — not just a style preference.
- Do NOT set assessed_level unless highly confident from specific structures in the sentence. When uncertain, omit and describe complexity in complexity_note.
- ALWAYS include complexity_note describing THIS sentence's structures.
- next_level_alt MUST rewrite the sentence at a higher level — never copy the input verbatim.
- tip MUST include at least one complete example sentence in ${langName} showing a stronger phrasing.
- ALL example sentences (correction, next_level_alt, target_level_alt) MUST be COMPLETE SENTENCES written in ${langName}, NEVER in English. Do NOT return short labels or descriptions — return full, natural sentences.
- next_level_alt and target_level_alt must express the SAME idea as the original sentence rephrased with grammar and vocabulary appropriate for that CEFR level. Do NOT add new information or embellish.
- grammar_rule, explanation, register, and tip must be in English.

MULTIPLE ERRORS (very important for Browser AI):
- If the sentence has more than one mistake, list EVERY error in explanation as separate bullet points (•), quoting the learner's exact words.
- Each bullet must name the rule AND the fix (e.g. "«muchos cosas» → «muchas cosas» (gender agreement)").
- Do NOT bury fixes only inside next_level_alt — when status is "Needs Improvement", correction is REQUIRED: one full corrected sentence at the learner's level.
- Do NOT replace explanation with a single rewritten sentence — explain each error clearly in English first.
- next_level_alt and target_level_alt MUST be plain JSON strings (never nested objects).

Respond with ONLY a valid JSON object. No markdown fences, no text outside the JSON, no <think> tags:
{
  "assessed_level": "A1" | "A2" | "B1" | "B2" | "C1" | "C2" | null,
  "complexity_note": "1–2 English sentences on sentence complexity (vocabulary, syntax, subordination, register)",
  "status": "Excellent" or "Needs Improvement",
  "grammar_rule": "The specific grammar rule tested or applied — always explain, even when correct",
  "explanation": "WHY the sentence is correct or incorrect — be specific and actionable",
  "correction": null or "Corrected sentence in ${langName} (only if Needs Improvement)",
  "register": "State the register as one declarative phrase — e.g. 'informal (${informalRegister}) — casual; shift to ${formalRegister} in clinical/legal settings' OR 'formal (${formalRegister}) — appropriate for professional interpreting'. Read the pronouns/verb endings IN THIS SENTENCE; do NOT default to formal just because the context is professional. Do NOT write meta-instructions like 'Note whether…'.",
  "next_level_alt": "COMPLETE SENTENCE in ${langName}: same idea one CEFR level above assessed_level, or null if no assessed_level",
  "target_level_alt": "COMPLETE SENTENCE in ${langName}: two levels above assessed_level, or null",
  "tip": "One concrete tip for an interpreter trainee. REQUIRED: include one complete ${langName} example sentence. Format: tip sentence. E.g. «complete ${langName} example here». Never write 'Apply each fix' or other generic advice."
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

// ── API CALL: Parlance fine-tuned SLM (local server) ─────────────
async function callParlanceSLM(sentence, language, ragContext = '') {
  const base = PARLANCE_SLM_URL.replace(/\/$/, '');
  const resp = await fetch(`${base}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sentence, language, ragContext }),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error(data.error || `Parlance SLM server error (${resp.status})`);
  }
  if (!data.feedback) throw new Error('No feedback from Parlance SLM server');
  return JSON.stringify(data.feedback);
}

function isNativeParlanceApp() {
  return !!(window.__PARLANCE_CONFIG__ && window.webkit?.messageHandlers?.parlance);
}

function parlanceAuthSignedIn() {
  return isFirebaseSignedIn();
}

function effectiveRequiresKey(providerId) {
  if (isFirebaseSignedIn() && isCloudProvider(providerId)) return false;
  return AI_PROVIDERS[providerId]?.requiresKey ?? false;
}

function parlanceCoachAvailableForLanguage(language) {
  const cfg = window.__PARLANCE_CONFIG__ || {};
  const langs = cfg.parlanceCoachLanguages || (cfg.parlanceCoachAvailable ? ['es', 'fr'] : []);
  return langs.includes(language);
}

/** SLM storage id for journal language (es → parlance-es, fr → parlance-fr). */
function parlanceModelIdForLanguage(lang) {
  return lang === 'fr' ? 'parlance-fr' : 'parlance-es';
}

/** On iOS with bundled coach, model follows journal language — not a manual dual picker. */
function parlanceCoachModelFollowsJournal() {
  const cfg = window.__PARLANCE_CONFIG__ || {};
  return cfg.parlanceCoachAvailable && isNativeParlanceApp();
}

function parlanceCoachDisplayName(lang) {
  return 'Parlance Coach';
}

/** Keep localStorage parlance model aligned with state.currentLanguage on native iOS. */
function syncParlanceModelToJournalLanguage() {
  if (!parlanceCoachModelFollowsJournal()) return null;
  const modelId = parlanceModelIdForLanguage(state.currentLanguage);
  if (getProviderModel('parlance') !== modelId) {
    setProviderModel('parlance', modelId);
  }
  return modelId;
}

function unloadNativeParlanceSLM() {
  if (!isNativeParlanceApp()) return;
  try {
    window.webkit?.messageHandlers?.parlance?.postMessage({ action: 'unloadParlanceSLM' });
  } catch (_) {}
}

function buildRAGMeta(language, level, sentence, condensed = false) {
  if (typeof getRAGContextWithMeta === 'function') {
    return getRAGContextWithMeta(language, level, sentence, { condensed });
  }
  const context = typeof getRAGContext === 'function'
    ? getRAGContext(language, level, sentence, { condensed }) : '';
  return { context, topics: [] };
}

function attachRAGMeta(result, topics) {
  if (topics?.length) result._rag_topics = topics;
  return result;
}

function callNativeParlanceSLM(sentence, language, ragContext = '') {
  return new Promise((resolve, reject) => {
    const requestId = 'slm_' + Date.now() + '_' + Math.random().toString(36).slice(2);
    const timeoutId = setTimeout(() => {
      reject(new Error(parlanceTimeoutMessage(true)));
    }, TIMEOUT_MS.parlanceNative);
    window.__parlanceSLMResult = (id, result, err) => {
      if (id !== requestId) return;
      clearTimeout(timeoutId);
      delete window.__parlanceSLMResult;
      if (err) reject(new Error(err));
      else resolve(JSON.stringify(result));
    };
    window.webkit.messageHandlers.parlance.postMessage({
      action: 'analyzeParlanceSLM',
      requestId,
      sentence,
      language,
      ragContext,
    });
  });
}

function parlanceTimeoutMessage(nativeOnDevice) {
  if (nativeOnDevice) {
    return 'Parlance Coach is still working. The first on-device run can take 1–2 minutes while the model loads — keep the app open and wait, or try a shorter sentence.';
  }
  return 'Parlance Coach timed out. Check that the dev server is running, or switch provider in ⚙ AI.';
}

function analysisTimeoutMs(providerId) {
  if (providerId === 'parlance') {
    return isNativeParlanceApp() ? TIMEOUT_MS.parlanceNative : TIMEOUT_MS.parlanceServer;
  }
  if (providerId === 'webllm') return TIMEOUT_MS.webllm;
  return TIMEOUT_MS.cloud;
}

function analysisTimeoutMessage(providerId) {
  if (providerId === 'parlance') {
    return parlanceTimeoutMessage(isNativeParlanceApp());
  }
  const provider = AI_PROVIDERS[providerId];
  return `${provider?.name || 'AI'} timed out. Check your connection or try another provider in ⚙ AI.`;
}

async function checkParlanceSLMServer() {
  try {
    const base = PARLANCE_SLM_URL.replace(/\/$/, '');
    const resp = await fetch(`${base}/health`, { signal: AbortSignal.timeout(2000) });
    if (!resp.ok) return false;
    const data = await resp.json().catch(() => ({}));
    return data.spanish_ready === true || data.french_ready === true;
  } catch (_) {
    return false;
  }
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

  const jsonStr = cleaned.slice(start, end + 1)
    .replace(/,\s*}/g, '}')
    .replace(/,\s*]/g, ']');
  return JSON.parse(jsonStr);
}

function normalizeResult(raw, sentence = '', language = 'es') {
  const result = {};
  const assessed = extractAssessedLevel(raw);
  if (assessed) result.assessed_level = assessed;
  const complexity = extractComplexityNote(raw);
  if (complexity) result.complexity_note = complexity;
  result.status      = (raw.status === 'Excellent' || raw.status === 'Needs Improvement')
    ? raw.status : 'Excellent';
  result.grammar_rule = raw.grammar_rule || raw.grammarRule || 'Grammar rule not identified';
  result.explanation  = raw.explanation  || '';
  if (raw.correction)       result.correction      = raw.correction;
  if (raw.register)         result.register        = raw.register;
  if (raw.next_level_alt)   result.next_level_alt  = raw.next_level_alt;
  if (raw.target_level_alt) result.target_level_alt = raw.target_level_alt;
  if (raw.tip)              result.tip             = raw.tip;
  if (raw._coach_warning)   result._coach_warning  = raw._coach_warning;
  if (raw._coach_repaired)  result._coach_repaired = raw._coach_repaired;
  if (raw._rag_topics)      result._rag_topics     = raw._rag_topics;
  return sentence ? sanitizeFeedbackResult(sentence, result, language) : result;
}

// ── UNIFIED ANALYSIS ─────────────────────────────────────────────
// Called by analyzeSentence() — routes to the selected provider
async function analyzeWithAI(sentence, language, progressCallback) {
  // Check offline cache first
  try {
    const cacheKey = 'parlance_analysis_cache';
    const cache = JSON.parse(localStorage.getItem(cacheKey) || '{}');
    const hash = analysisCacheHash(sentence, language);
    if (cache[hash]) {
      return {
        ...sanitizeFeedbackResult(sentence, cache[hash].feedback, language),
        _cachedSource: (cache[hash].source || 'cached') + ' (cached)',
      };
    }
  } catch (_) {}

  const providerId = getSelectedProvider();
  const provider   = AI_PROVIDERS[providerId];
  if (!provider) throw new Error('Unknown AI provider');

  if (shouldUseFirebaseCloud(providerId)) {
    const ragMeta = buildRAGMeta(language, null, sentence, false);
    const timeoutMs = analysisTimeoutMs(providerId);
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error(analysisTimeoutMessage(providerId))), timeoutMs)
    );
    let result = await Promise.race([
      callFirebaseCloudAnalyze(sentence, language, providerId),
      timeoutPromise,
    ]);
    if (ragMeta.topics.length) attachRAGMeta(result, ragMeta.topics);
    result = sanitizeFeedbackResult(sentence, result, language);
    try {
      const cacheKey = 'parlance_analysis_cache';
      const cache = JSON.parse(localStorage.getItem(cacheKey) || '{}');
      const hash = analysisCacheHash(sentence, language);
      cache[hash] = { feedback: result, source: `${provider.name} (account)`, ts: Date.now() };
      const keys = Object.keys(cache);
      if (keys.length > 200) {
        const sorted = keys.sort((a, b) => cache[a].ts - cache[b].ts);
        sorted.slice(0, keys.length - 200).forEach(k => delete cache[k]);
      }
      localStorage.setItem(cacheKey, JSON.stringify(cache));
    } catch (_) {}
    return result;
  }

  const ragMeta     = buildRAGMeta(language, null, sentence, providerId === 'parlance');
  const ragContext  = ragMeta.context;
  const langName    = parlanceLanguageInfo(language).coachRole;
  const systemPrompt = buildSystemPrompt(langName, ragContext);
  const userMessage  = `Analyze this ${langName} sentence: "${sentence}"`;

  const timeoutMs = analysisTimeoutMs(providerId);
  const timeoutPromise = new Promise((_, reject) =>
    setTimeout(() => reject(new Error(analysisTimeoutMessage(providerId))), timeoutMs)
  );

  const analysisPromise = (async () => {
    let rawContent;

    if (providerId === 'parlance') {
      if (isNativeParlanceApp() && !parlanceCoachAvailableForLanguage(language)) {
        throw new Error(`Parlance Coach model is not bundled in this build. Run ./training/prepare_ios_coach_model.sh and re-archive, or use another provider in ⚙ AI.`);
      }
      if (isNativeParlanceApp()) {
        const nativeRaw = await callNativeParlanceSLM(sentence, language, ragContext);
        // Native bridge returns pre-validated JSON from ParlanceSLMFeedbackValidator.
        const nativeParsed = typeof nativeRaw === 'string' ? JSON.parse(nativeRaw) : nativeRaw;
        return attachRAGMeta(normalizeResult(nativeParsed, sentence, language), ragMeta.topics);
      }
      rawContent = await callParlanceSLM(sentence, language, ragContext);

    } else if (providerId === 'webllm') {
      if (!navigator.gpu) {
        throw new Error('Your browser does not support WebGPU (needed for Browser AI). Switch to a cloud provider like Groq (free) in ⚙ AI settings.');
      }
      const modelId = getProviderModel('webllm');
      const engine  = await ensureWebLLM(modelId, progressCallback);
      rawContent    = await callWebLLM(engine, systemPrompt, userMessage);

    } else if (providerId === 'anthropic') {
      const key   = getProviderKey('anthropic');
      if (effectiveRequiresKey('anthropic') && !key) {
        throw new Error('No Anthropic API key. Add one in ⚙ AI settings.');
      }
      rawContent  = await callAnthropic(getProviderModel('anthropic'), key, systemPrompt, userMessage);

    } else if (providerId === 'gemini') {
      const key   = getProviderKey('gemini');
      if (effectiveRequiresKey('gemini') && !key) {
        throw new Error('No Gemini API key. Add one in ⚙ AI settings.');
      }
      rawContent  = await callGemini(getProviderModel('gemini'), key, systemPrompt, userMessage);

    } else {
      // OpenAI-compatible: groq, openai, kimi, deepseek, openrouter
      const key   = getProviderKey(providerId);
      if (effectiveRequiresKey(providerId) && !key) {
        throw new Error(`No ${provider.name} API key. Add one in ⚙ AI settings.`);
      }
      rawContent  = await callOpenAIFormat(
        provider.endpoint, getProviderModel(providerId), key, systemPrompt, userMessage
      );
    }

    return rawContent;
  })();

  const analysisResult = await Promise.race([analysisPromise, timeoutPromise]);
  let result = (typeof analysisResult === 'object' && analysisResult?.status)
    ? sanitizeFeedbackResult(sentence, analysisResult, language)
    : normalizeResult(parseAIContent(analysisResult), sentence, language);
  if (ragMeta.topics.length && !result._rag_topics) {
    attachRAGMeta(result, ragMeta.topics);
  }

  // Cache the analysis result in localStorage
  try {
    const cacheKey = 'parlance_analysis_cache';
    const cache = JSON.parse(localStorage.getItem(cacheKey) || '{}');
    const hash = analysisCacheHash(sentence, language);
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
// Locale data lives in locales/*.json — loaded by i18n.js module.
// HTML elements use data-i18n attributes for declarative binding.
// To add a language: create locales/xx.json and add an <option> to #uiLangSelect.

function updateDateBadge() {
  const locale = (typeof i18n !== 'undefined' && i18n.getLocale) ? i18n.getLocale() : 'en';
  const localeTag = locale === 'es' ? 'es' : locale === 'fr' ? 'fr' : 'en-US';
  document.getElementById('dateBadge').textContent = new Date()
    .toLocaleDateString(localeTag, { month: 'short', day: 'numeric', year: 'numeric' });
}

function refreshOpenGuideLanguage() {
  const overlay = document.getElementById('guideOverlay');
  const frame = document.getElementById('guideFrame');
  if (!overlay || overlay.style.display === 'none' || !frame?.src) return;
  const ui = document.getElementById('uiLangSelect')?.value
    || ((typeof i18n !== 'undefined' && i18n.getLocale) ? i18n.getLocale() : 'en');
  const theme = document.documentElement.getAttribute('data-theme') || 'light';
  try {
    frame.contentWindow?.postMessage({ type: 'parlanceGuideEnv', ui, theme }, '*');
    if (typeof frame.contentWindow?.applyGuideEnv === 'function') {
      frame.contentWindow.applyGuideEnv(ui, theme);
    }
  } catch (_) { /* ignore */ }
}

/** Refresh every dynamic UI surface that locales don't cover via data-i18n. */
function refreshDynamicI18nUI() {
  if (!document.getElementById('uiLangSelect')) return;
  updateCounts();
  renderPrompts();
  updateDateBadge();
  updateWaitingCard();
  document.querySelectorAll('.analyze-btn').forEach(btn => {
    btn.textContent = i18n.t('getFeedback');
  });
  document.querySelectorAll('.sentence-input').forEach(ta => {
    const hint = i18n.t('analyzeHint');
    if (hint && hint !== 'analyzeHint') ta.title = hint;
  });
  const loadAll = document.getElementById('loadAllToEditorBtn');
  if (loadAll) loadAll.textContent = i18n.t('loadAllToEditor');
  refreshOpenGuideLanguage();
}

function onUILangChange() {
  const lang = document.getElementById('uiLangSelect').value;
  i18n.load(lang);
}

if (typeof i18n !== 'undefined' && i18n.onChange) {
  i18n.onChange(refreshDynamicI18nUI);
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
// Single source of truth lives in languages.js (PARLANCE_LANGUAGES) — loaded before
// this file. Keep the `languages` name here since it's used throughout this file.
const languages = PARLANCE_LANGUAGES;

// ── STATE ─────────────────────────────────────────────────────────
const state = {
  sentences: [],
  activeSentenceId: null,
  analyzingSentenceIds: new Set(),
  savedEntries: [],
  isOnline: navigator.onLine,
  currentLanguage: 'es',
};

// ── AI SETTINGS UI ────────────────────────────────────────────────
let modalSelectedProvider = 'webllm';

function openAISettings() {
  if (isNativeParlanceApp() && window.webkit?.messageHandlers?.parlance) {
    window.webkit.messageHandlers.parlance.postMessage('showAISettings');
    return;
  }
  syncParlanceModelToJournalLanguage();
  modalSelectedProvider = getSelectedProvider();
  renderProviderGrid();
  updateFirebaseAuthUI();
  updateModalForProvider(modalSelectedProvider);
  document.getElementById('aiSettingsOverlay').style.display = 'flex';
}

/** Called from iOS after native AI Settings sheet closes. */
function applyNativeAISettings(providerId, model) {
  if (providerId && AI_PROVIDERS[providerId]) {
    setSelectedProvider(providerId);
    if (model) setProviderModel(providerId, model);
  }
  updateFirebaseAuthUI();
  updateWaitingCard();
}

function callNativeAuth(action) {
  return new Promise((resolve, reject) => {
    if (!isNativeParlanceApp()) {
      reject(new Error('Not in native app'));
      return;
    }
    const requestId = 'auth_' + Date.now() + '_' + Math.random().toString(36).slice(2);
    const timeoutId = setTimeout(() => {
      delete window.__parlanceAuthResult;
      reject(new Error('Sign-in timed out'));
    }, 120000);
    window.__parlanceAuthResult = (id, err) => {
      if (id !== requestId) return;
      clearTimeout(timeoutId);
      delete window.__parlanceAuthResult;
      if (err) reject(new Error(err));
      else resolve();
    };
    window.webkit.messageHandlers.parlance.postMessage({ action, requestId });
  });
}

function closeAISettings() {
  document.getElementById('aiSettingsOverlay').style.display = 'none';
}

// ── Call pack purchase ────────────────────────────────────────────────────────

function triggerCallPackPurchase() {
  if (!isNativeParlanceApp()) {
    showErrorInPanel('Monthly limit reached (30 calls). Get 100 more calls for $0.99 in the app.');
    return;
  }
  const requestId = 'purchase_' + Date.now() + '_' + Math.random().toString(36).slice(2);
  window.__parlancePurchaseResult = (id, data, err) => {
    if (id !== requestId) return;
    delete window.__parlancePurchaseResult;
    if (err === 'cancelled') {
      showToast(i18n.t('purchaseCancelled'));
      return;
    }
    if (err) {
      showErrorInPanel('Purchase failed: ' + err + '. You can try again or switch to Parlance Coach in Settings.');
      return;
    }
    refreshUsageDisplay();
    showToast(i18n.t('callPackAdded'));
  };
  window.webkit.messageHandlers.parlance.postMessage({ action: 'purchaseCallPack', requestId });
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
      if (p.id === 'parlance') syncParlanceModelToJournalLanguage();
      updateModalForProvider(p.id);
    });
    grid.appendChild(card);
  });
}

function updateModalForProvider(id) {
  const provider = AI_PROVIDERS[id];

  const cloudNote = document.getElementById('authCloudNote');
  if (cloudNote) {
    cloudNote.style.display = (isFirebaseSignedIn() && isCloudProvider(id)) ? '' : 'none';
  }

  // API key section
  const keySection  = document.getElementById('apiKeySection');
  const apiKeyInput = document.getElementById('apiKeyInput');
  const apiKeyHint  = document.getElementById('apiKeyHint');
  if (effectiveRequiresKey(id)) {
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

  // Model dropdown (native iOS Parlance Coach: single model tied to journal language)
  const modelSection = document.getElementById('modelSection');
  const modelSel = document.getElementById('modalModelSelect');
  modelSel.innerHTML = '';
  if (id === 'parlance' && parlanceCoachModelFollowsJournal()) {
    const modelId = syncParlanceModelToJournalLanguage();
    modelSection.style.display = 'none';
    const opt = document.createElement('option');
    opt.value = modelId;
    opt.textContent = parlanceCoachDisplayName(state.currentLanguage);
    opt.selected = true;
    modelSel.appendChild(opt);
  } else {
    modelSection.style.display = '';
    const savedModel = getProviderModel(id);
    provider.models.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m.id;
      opt.textContent = m.name;
      opt.selected = m.id === savedModel;
      modelSel.appendChild(opt);
    });
  }

  // CORS warning
  document.getElementById('corsWarning').style.display = provider.corsNote ? '' : 'none';
}

function saveAISettingsFromModal() {
  const id    = modalSelectedProvider;
  let model   = document.getElementById('modalModelSelect').value;
  const key   = document.getElementById('apiKeyInput').value.trim();

  if (id === 'parlance' && parlanceCoachModelFollowsJournal()) {
    model = syncParlanceModelToJournalLanguage();
  }

  setSelectedProvider(id);
  setProviderModel(id, model);
  if (effectiveRequiresKey(id) && key) setProviderKey(id, key);

  // Reset engine if WebLLM model changed
  if (id === 'webllm' && webLLMCurrentModelId !== model) {
    webLLMEngine = null;
    webLLMCurrentModelId = null;
  }

  closeAISettings();
  updateWaitingCard();
  showToast(i18n.t('providerSet', { name: AI_PROVIDERS[id].name }));
}

// ── PLATFORM DETECTION ────────────────────────────────────────────
const isCapacitor = !!(window.Capacitor);
const isAndroid   = isCapacitor && window.Capacitor.getPlatform?.() === 'android';
const hasWebGPU   = !!navigator.gpu;
const canUseWebLLM = hasWebGPU && !isCapacitor;

// ── INIT ──────────────────────────────────────────────────────────
async function init() {
  initTheme();
  await i18n.init();
  await ensureFirebaseReady().catch(() => {});
  updateFirebaseAuthUI();
  document.getElementById('uiLangSelect').value = i18n.getLocale();
  updateDateBadge();

  const savedLang = localStorage.getItem('parlance_language') || 'es';
  state.currentLanguage = savedLang;
  document.getElementById('langSelect').value = savedLang;
  if (getSelectedProvider() === 'parlance') {
    syncParlanceModelToJournalLanguage();
  }

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

  // iOS app with bundled MLX coach: default to Parlance Coach
  const cfg = window.__PARLANCE_CONFIG__ || {};
  if (cfg.parlanceCoachAvailable && isNativeParlanceApp()) {
    setSelectedProvider('parlance');
    syncParlanceModelToJournalLanguage();
    updateWaitingCard();
  } else if (await checkParlanceSLMServer()) {
    // Web / dev: Mac Python server
    setSelectedProvider('parlance');
    updateWaitingCard();
  }

  // On Android/Capacitor with no cloud provider configured, prompt AI settings
  if (!canUseWebLLM && getSelectedProvider() === 'webllm') {
    setTimeout(() => openAISettings(), 500);
  }
}

function updateWaitingCard() {
  const id   = getSelectedProvider();
  const p    = AI_PROVIDERS[id];
  const hint = document.getElementById('waitingProviderHint');
  if (!hint || !p || typeof i18n === 'undefined') return;

  const linkStyle = 'background:none;border:none;color:var(--accent);font-family:inherit;font-size:inherit;cursor:pointer;padding:0;text-decoration:underline';
  const settingsBtn = (label) =>
    `<button type="button" onclick="openAISettings()" style="${linkStyle}">${label}</button>`;

  if (id === 'parlance') {
    const cfg = window.__PARLANCE_CONFIG__ || {};
    const lang = state.currentLanguage;
    if (cfg.parlanceCoachAvailable && isNativeParlanceApp()) {
      const key = parlanceCoachAvailableForLanguage(lang)
        ? 'waitingParlanceOnDevice'
        : 'waitingParlanceMissing';
      hint.innerHTML = i18n.t(key, { icon: p.icon });
    } else {
      hint.innerHTML = i18n.t('waitingParlanceServer', { icon: p.icon });
    }
  } else if (id === 'webllm') {
    if (canUseWebLLM) {
      hint.innerHTML = i18n.t('waitingWebLLM', { icon: p.icon });
    } else {
      hint.innerHTML = `⚙ ${settingsBtn(i18n.t('waitingSetupProvider'))}`;
    }
  } else if (isFirebaseSignedIn() && isCloudProvider(id)) {
    hint.innerHTML = i18n.t('waitingCloudReady', { icon: p.icon, name: p.name });
  } else if (getProviderKey(id)) {
    hint.innerHTML = i18n.t('waitingProviderWrite', { icon: p.icon, name: p.name });
  } else {
    hint.innerHTML = `⚙ ${settingsBtn(i18n.t('waitingAddKey', { name: p.name }))}`;
  }
}

// ── LANGUAGE SWITCHING ────────────────────────────────────────────
function onLanguageChange() {
  const prevModel = getProviderModel('parlance');
  state.currentLanguage = document.getElementById('langSelect').value;
  localStorage.setItem('parlance_language', state.currentLanguage);
  updatePlaceholders();
  renderPrompts();
  loadGuide();

  if (getSelectedProvider() === 'parlance') {
    syncParlanceModelToJournalLanguage();
    if (parlanceCoachModelFollowsJournal() && prevModel !== getProviderModel('parlance')) {
      unloadNativeParlanceSLM();
    }
    updateWaitingCard();
  }
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
  // Update privacy modal content with current UI language
  const overlay = document.getElementById('privacyOverlay');
  const header = overlay.querySelector('.modal-header h2');
  if (header) header.textContent = i18n.t('privacyTitle');

  const body = overlay.querySelector('.modal-body');
  if (body) {
    body.innerHTML = `
      <div class="privacy-section">
        <h3>${i18n.t('privacyWritingTitle')}</h3>
        <p>${i18n.t('privacyWritingText')}</p>
      </div>
      <div class="privacy-section">
        <h3>${i18n.t('privacyAITitle')}</h3>
        <p><strong>${i18n.t('privacyAIText1')}</strong></p>
        <p style="margin-top:0.5rem">${i18n.t('privacyAIText2')}</p>
      </div>
      <div class="privacy-section">
        <h3>${i18n.t('privacyKeysTitle')}</h3>
        <p>${i18n.t('privacyKeysText')}</p>
      </div>
      <div class="privacy-section">
        <h3>${i18n.t('privacyTrackingTitle')}</h3>
        <p>${i18n.t('privacyTrackingText')}</p>
      </div>
      <div class="privacy-updated">${i18n.t('privacyUpdated')}</div>
    `;
  }

  overlay.style.display = 'flex';
}

function closePrivacyPolicy() {
  document.getElementById('privacyOverlay').style.display = 'none';
}

// ── PROMPTS ───────────────────────────────────────────────────────
function renderPrompts() {
  const list = document.getElementById('promptList');
  list.innerHTML = '';
  const langCode = state.currentLanguage;
  for (let n = 1; n <= 7; n++) {
    const text = i18n.t(`prompts_${langCode}_${n}`);
    if (text === `prompts_${langCode}_${n}`) continue;
    const el = document.createElement('div');
    el.className = 'prompt-item';
    el.textContent = text;
    el.setAttribute('role', 'button');
    el.tabIndex = 0;
    el.onclick = () => usePrompt(text);
    el.onkeydown = (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); usePrompt(text); }
    };
    list.appendChild(el);
  }
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

function addSentence(prefill = '', opts = {}) {
  const { insertAt = null, focus = true } = opts;
  const id       = ++sentenceIdCounter;
  const sentence = { id, text: '', feedback: null, status: 'empty' };

  if (insertAt == null || insertAt >= state.sentences.length) {
    state.sentences.push(sentence);
  } else {
    state.sentences.splice(insertAt, 0, sentence);
  }

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
        rows="3"
        spellcheck="false"
        data-i18n-title="analyzeHint"
        title="Write freely. ⌘Enter / Ctrl+Enter for feedback."
      ></textarea>
      <div class="sentence-actions">
        <button type="button" class="analyze-btn" id="analyze-btn-${id}" data-i18n="getFeedback" title="Get feedback">Feedback</button>
        <div class="sentence-status" id="status-${id}"></div>
      </div>
    </div>
  `;

  if (insertAt == null || insertAt >= state.sentences.length - 1) {
    area.appendChild(row);
  } else {
    const afterId = state.sentences[insertAt + 1]?.id;
    const nextRow = afterId ? document.getElementById('row-' + afterId) : null;
    if (nextRow) area.insertBefore(row, nextRow);
    else area.appendChild(row);
  }

  const ta = row.querySelector('textarea');
  const analyzeBtn = row.querySelector('.analyze-btn');
  ta.addEventListener('input', () => onSentenceInput(id));
  ta.addEventListener('keydown', (e) => onSentenceKeydown(e, id));
  ta.addEventListener('focus', () => { state.activeSentenceId = id; showFeedback(id); });
  ta.addEventListener('input', () => {
    ta.style.height = 'auto';
    ta.style.height = Math.max(ta.scrollHeight, 72) + 'px';
  });
  analyzeBtn.addEventListener('click', () => {
    state.activeSentenceId = id;
    analyzeSentence(id);
  });
  if (typeof i18n !== 'undefined' && i18n.apply) {
    analyzeBtn.textContent = i18n.t('getFeedback');
    const hint = i18n.t('analyzeHint');
    if (hint && hint !== 'analyzeHint') ta.title = hint;
  }

  if (prefill) {
    ta.value = prefill;
    sentence.text = prefill;
    sentence.status = 'dirty';
    ta.dispatchEvent(new Event('input'));
  }

  updateCounts();
  if (focus) setTimeout(() => ta.focus(), 50);
  return id;
}

function sentenceReadyToAnalyze(text) {
  const trimmed = text.trim();
  if (trimmed.length < MIN_SENTENCE_CHARS) return false;
  const words = trimmed.split(/\s+/).filter(Boolean);
  return words.length >= MIN_SENTENCE_WORDS;
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
}

function onSentenceKeydown(e, id) {
  // Enter inserts a new line so people can write paragraphs.
  // ⌘Enter / Ctrl+Enter requests feedback for this block.
  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
    e.preventDefault();
    const ta   = document.getElementById('ta-' + id);
    const text = ta.value.trim();
    if (sentenceReadyToAnalyze(text) || splitIntoSentences(text).some(sentenceReadyToAnalyze)) {
      state.activeSentenceId = id;
      analyzeSentence(id);
    }
  }
}

function updateCounts() {
  const filled = state.sentences.filter(s => s.text.trim());
  const sentenceUnits = filled.reduce(
    (acc, s) => acc + Math.max(1, countSentencesInText(s.text)), 0
  );
  document.getElementById('sentenceCount').textContent =
    i18n.tc('sentenceCount', sentenceUnits);
  const words = filled.reduce(
    (acc, s) => acc + s.text.trim().split(/\s+/).filter(Boolean).length, 0
  );
  document.getElementById('wordCount').textContent =
    i18n.tc('wordCount', words);

  state.sentences.forEach((s, i) => {
    const num = document.querySelector(`#row-${s.id} .sentence-num`);
    if (num) num.textContent = i + 1;
  });
}

// ── ANALYSIS ──────────────────────────────────────────────────────
async function analyzeSentence(id) {
  const sentence = state.sentences.find(s => s.id === id);
  if (!sentence) return;
  if (state.analyzingSentenceIds.has(id)) return;

  // If the box holds a full paragraph, split into sentence rows first so
  // each one still gets its own feedback card.
  const parts = splitIntoSentences(sentence.text).filter(p => p.trim());
  if (parts.length > 1) {
    const idx = state.sentences.findIndex(s => s.id === id);
    const ta0 = document.getElementById('ta-' + id);
    sentence.text = parts[0];
    sentence.feedback = null;
    sentence.status = 'dirty';
    if (ta0) {
      ta0.value = parts[0];
      ta0.style.height = 'auto';
      ta0.style.height = Math.max(ta0.scrollHeight, 72) + 'px';
    }
    const extraIds = [];
    for (let i = 1; i < parts.length; i++) {
      extraIds.push(addSentence(parts[i], { insertAt: idx + i, focus: false }));
    }
    updateCounts();
    await analyzeSentence(id);
    for (const extraId of extraIds) {
      await analyzeSentence(extraId);
    }
    return;
  }

  if (!sentenceReadyToAnalyze(sentence.text)) return;

  state.analyzingSentenceIds.add(id);

  const ta       = document.getElementById('ta-' + id);
  const statusEl = document.getElementById('status-' + id);
  ta.classList.add('analyzing');
  ta.classList.remove('has-error', 'is-great');
  statusEl.textContent = '⏳';

  showAnalyzingState(id);

  const providerId = getSelectedProvider();

  try {
    const result = await analyzeWithAI(
      sentence.text,
      state.currentLanguage,
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

    // Friendly message for rate-limit and auth errors from Firebase Functions
    const code = err.code || '';
    let msg = err.message || 'Could not analyze — check your settings.';
    if (code === 'functions/resource-exhausted' || msg.includes('Monthly free limit')) {
      refreshUsageDisplay();
      triggerCallPackPurchase();
      return;
    } else if (code === 'functions/unauthenticated') {
      msg = 'Sign in to use cloud AI providers — tap ⚙ AI.';
    }

    showErrorInPanel(msg);
    showToast(msg.length > 80 ? msg.slice(0, 80) + '…' : msg);
  } finally {
    state.analyzingSentenceIds.delete(id);
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
  document.querySelectorAll('.feedback-tab').forEach(t => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
  document.getElementById('feedbackInner').style.display  = tab === 'feedback' ? 'flex' : 'none';
  document.getElementById('promptsInner').style.display   = tab === 'prompts'  ? 'flex' : 'none';
  document.getElementById('guideInner').style.display     = tab === 'guide'    ? 'flex' : 'none';
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
  const providerId = getSelectedProvider();
  let analyzingKey = 'analyzing';
  if (providerId === 'parlance') {
    analyzingKey = isNativeParlanceApp() ? 'analyzingParlanceOnDevice' : 'analyzingParlanceServer';
  }
  card.innerHTML = `
    <div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
    <div class="analyzing-text">${i18n.t(analyzingKey)}</div>
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
  const assessedLevel = extractAssessedLevel(fb);
  const complexityNote = extractComplexityNote(fb);
  const { nextLabel, targetLabel } = altVersionLabels(assessedLevel);

  let body = '';
  if (assessedLevel) {
    body += feedbackItem('label-level', i18n.t('assessedLevelLabel'), i18n.t('assessedLevelRichText', { level: assessedLevel }));
  }
  if (complexityNote) {
    body += feedbackItem('label-complexity', i18n.t('complexityNoteLabel'), complexityNote);
  }
  body += feedbackItem('label-rule',         '📐 Grammar Rule',  fb.grammar_rule);
  if (fb.correction && !isExcellent) {
    body += feedbackItem('label-correction', '✍ Corrected Sentence', fb.correction);
  }
  body += feedbackItem(
    'label-explanation',
    isExcellent ? '✨ Why This Works' : '⚠ What Needs Work',
    fb.explanation
  );
  if (fb.correction && isExcellent) {
    body += feedbackItem('label-correction', '✍ Corrected Sentence', fb.correction);
  }
  if (fb.register)         body += feedbackItem('label-register',   '🎭 Register',               fb.register);
  if (fb.next_level_alt)   body += feedbackItem('label-next',       `🔼 ${nextLabel} Version`,   fb.next_level_alt);
  if (fb.target_level_alt && targetLabel)
                           body += feedbackItem('label-target',     `🎯 ${targetLabel} Version`, fb.target_level_alt);
  if (fb.tip)              body += feedbackItem('label-tip',        '💡 Tip',                    fb.tip);
  if (fb._coach_warning) {
    body += `<div class="feedback-coach-warning">${escapeHTML(fb._coach_warning)}</div>`;
  }
  if (fb._rag_topics?.length) {
    const chips = fb._rag_topics.map(t =>
      `<span class="feedback-rag-chip">${escapeHTML(t)}</span>`
    ).join('');
    body += `<div class="feedback-rag-topics"><span class="feedback-rag-label">Reference</span>${chips}</div>`;
  }

  const sourceLabel = sentence.analysisSource || 'AI';
  const idx         = state.sentences.findIndex(s => s.id === id) + 1;

  const card = document.createElement('div');
  card.className = 'feedback-card';
  card.innerHTML = `
    <div class="feedback-card-header">
      <div class="feedback-sentence-ref">Sentence ${idx}</div>
      <div class="feedback-header-badges">
        ${assessedLevel ? `<div class="feedback-level-badge" title="${escapeHTML(i18n.t('assessedLevelHint'))}">~${assessedLevel}</div>` : ''}
        <div class="feedback-score ${statusClass}">${statusLabel}</div>
        <div class="feedback-source">${escapeHTML(sourceLabel)}</div>
      </div>
    </div>
    <div class="feedback-original">"${escapeHTML(sentence.text)}"</div>
    <div class="feedback-body">${body}</div>
  `;
  inner.appendChild(card);
  inner.scrollTop = 0;
}

function feedbackItem(labelClass, label, text) {
  const display = (typeof ParlanceFeedbackSanitize !== 'undefined' && ParlanceFeedbackSanitize.coerceFeedbackText)
    ? (ParlanceFeedbackSanitize.coerceFeedbackText(text) || '')
    : String(text || '');
  if (!display.trim()) return '';
  return `
    <div class="feedback-item">
      <div class="feedback-item-label ${labelClass}">${label}</div>
      <div class="feedback-item-text">${escapeHTML(display)}</div>
    </div>
  `;
}

// ── GUIDE OVERLAY ─────────────────────────────────────────────────
function loadGuide() {
  // Called on language switch — resets the guide overlay
  const frame = document.getElementById('guideFrame');
  if (frame && frame.src) frame.src = '';
}

function openGuideOverlay(kind = 'grammar') {
  const lang    = currentLang();
  const overlay = document.getElementById('guideOverlay');
  const frame   = document.getElementById('guideFrame');
  const file = kind === 'dialect' ? lang.dialectFile : lang.guideFile;

  if (!file) { showToast(i18n.t('guideComingSoon')); return; }

  // Pass interface language so dialect pages show English when the app UI is
  // English. Prefer the live <select> value so a just-changed language sticks
  // even if i18n.locale hasn't finished reloading yet.
  const uiSelect = document.getElementById('uiLangSelect');
  const ui = (uiSelect && uiSelect.value)
    || ((typeof i18n !== 'undefined' && i18n.getLocale) ? i18n.getLocale() : 'en');
  const theme = document.documentElement.getAttribute('data-theme') || 'light';
  const qs = new URLSearchParams({ ui, theme });
  frame.src = `${file}?${qs.toString()}`;
  frame.onload = () => {
    try {
      frame.contentWindow?.postMessage({ type: 'parlanceGuideEnv', ui, theme }, '*');
      const doc = frame.contentDocument;
      if (doc?.body && typeof doc.defaultView?.applyGuideEnv === 'function') {
        doc.defaultView.applyGuideEnv(ui, theme);
      }
    } catch (_) { /* cross-origin safety */ }
    if (theme === 'dark') {
      frame.contentDocument?.documentElement?.setAttribute('data-theme', 'dark');
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
  if (!sentences.length) { showToast(i18n.t('writeFirst')); return; }

  const entry = {
    id:       Date.now(),
    title,
    language: state.currentLanguage,
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
  showToast(i18n.t('entrySaved') + ' ✓');
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
  const langName = parlanceLanguageInfo(entry.language).name;
  document.getElementById('entryViewerMeta').textContent =
    `${entry.date} · ${langName}`;

  const body = document.getElementById('entryViewerBody');
  body.innerHTML = '';

  // "Load All to Editor" button at the top
  const loadAllRow = document.createElement('div');
  loadAllRow.style.cssText = 'margin-bottom: 1rem; text-align: right;';
  const loadAllBtn = document.createElement('button');
  loadAllBtn.className = 'entry-load-btn';
  loadAllBtn.textContent = i18n.t('loadAllToEditor');
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
      const assessed = extractAssessedLevel(feedback);
      feedbackHTML = `
        <div class="entry-sentence-actions">
          <span class="entry-feedback-badge ${badgeClass}">${badgeLabel}</span>
          ${assessed ? `<span class="entry-feedback-badge" style="background:var(--blue-bg);color:var(--blue);">~${assessed}</span>` : ''}
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
      loadSentenceToEditor(text, entry.language);
    });

    body.appendChild(row);
  });

  document.getElementById('entryDeleteBtn').onclick = () => deleteEntry(entry.id);

  const overlay = document.getElementById('entryOverlay');
  overlay.style.display = 'flex';
  overlay.onclick = (e) => { if (e.target === overlay) closeEntryViewer(); };
}

function loadSentenceToEditor(text, language) {
  if (language) {
    state.currentLanguage = language;
    document.getElementById('langSelect').value = language;
    localStorage.setItem('parlance_language', language);
    updatePlaceholders();
    renderPrompts();
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
  if (entry.language) {
    state.currentLanguage = entry.language;
    document.getElementById('langSelect').value = entry.language;
    localStorage.setItem('parlance_language', entry.language);
    updatePlaceholders();
    renderPrompts();
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
  showToast(i18n.t('entryLoaded'));
}

function deleteEntry(entryId) {
  const idx = state.savedEntries.findIndex(e => e.id === entryId);
  if (idx === -1) return;
  state.savedEntries.splice(idx, 1);
  try { localStorage.setItem('parlance_entries', JSON.stringify(state.savedEntries)); } catch (_) {}
  closeEntryViewer();
  renderPastEntries();
  if (!state.savedEntries.length) document.getElementById('pastBar').style.display = 'none';
  showToast(i18n.t('entryDeleted'));
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
