// ── CONFIG (injected by Swift) ────────────────────────────────────
const parlanceConfig = window.__PARLANCE_CONFIG__ || { mode: 'direct', apiKey: '', proxyURL: '', onDeviceAvailable: false };

// ── ON-DEVICE BRIDGE ─────────────────────────────────────────────
const pendingOnDeviceRequests = {};
let onDeviceRequestCounter = 0;

window.__parlanceOnDeviceResult = function(requestId, result, error) {
  const pending = pendingOnDeviceRequests[requestId];
  if (!pending) return;
  delete pendingOnDeviceRequests[requestId];
  if (error) pending.reject(new Error(error));
  else pending.resolve(result);
};

function requestOnDeviceAnalysis(sentence, language, level) {
  return new Promise((resolve, reject) => {
    const requestId = 'od_' + (++onDeviceRequestCounter);
    pendingOnDeviceRequests[requestId] = { resolve, reject };
    window.webkit.messageHandlers.parlance.postMessage({
      action: 'analyzeOnDevice',
      requestId, sentence, language, level
    });
    setTimeout(() => {
      if (pendingOnDeviceRequests[requestId]) {
        delete pendingOnDeviceRequests[requestId];
        reject(new Error('On-device analysis timed out'));
      }
    }, 30000);
  });
}

// ── LANGUAGE DEFINITIONS ─────────────────────────────────────────
const languages = {
  es: {
    code: 'es',
    name: 'Español',
    placeholder: 'Escribe una oración en español…',
    titlePlaceholder: 'Entry title… (e.g. Mi primer día en Valencia)',
    coachRole: 'Spanish',
    guideFile: 'guide-es.html',
    prompts: [
      "Describe cómo fue tu primer día aprendiendo español.",
      "¿Qué significa ser intérprete para ti?",
      "Habla sobre un lugar que te gustaría visitar en España o Latinoamérica.",
      "Describe a una persona importante en tu vida.",
      "¿Cuáles son tus metas profesionales para este año?",
      "Escribe sobre una tradición cultural que te parece interesante.",
      "¿Qué opinas sobre la importancia de los idiomas en el mundo actual?",
    ]
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
      "Que signifie être interprète pour vous ?",
      "Parlez d'un endroit que vous aimeriez visiter en France ou en Afrique francophone.",
      "Décrivez une personne importante dans votre vie.",
      "Quels sont vos objectifs professionnels pour cette année ?",
      "Écrivez sur une tradition culturelle qui vous semble intéressante.",
      "Que pensez-vous de l'importance des langues dans le monde actuel ?",
    ]
  }
};

// ── STATE ─────────────────────────────────────────────────────────
const state = {
  sentences: [],
  activeSentenceId: null,
  analysisQueue: [],
  isAnalyzing: false,
  debounceTimers: {},
  entryCount: 0,
  savedEntries: [],
  isOnline: navigator.onLine,
  currentLanguage: 'es',
};

// ── INIT ──────────────────────────────────────────────────────────
function init() {
  document.getElementById('dateBadge').textContent = new Date()
    .toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' });

  const savedLang = localStorage.getItem('parlance_language') || 'es';
  state.currentLanguage = savedLang;
  document.getElementById('langSelect').value = savedLang;

  renderPrompts();
  addSentence();
  loadSavedEntries();
  initNetworkMonitor();
  updatePlaceholders();
}

// ── LANGUAGE SWITCHING ───────────────────────────────────────────
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

// ── NETWORK MONITOR ──────────────────────────────────────────────
function initNetworkMonitor() {
  updateOnlineStatus(navigator.onLine);
  window.addEventListener('online', () => updateOnlineStatus(true));
  window.addEventListener('offline', () => updateOnlineStatus(false));
  window.addEventListener('nativeNetworkChange', (e) => {
    updateOnlineStatus(e.detail.online);
  });
}

function updateOnlineStatus(online) {
  state.isOnline = online;
  const banner = document.getElementById('offlineBanner');
  if (online) {
    banner.classList.remove('show');
  } else {
    banner.classList.add('show');
  }
}

// ── PRIVACY POLICY ───────────────────────────────────────────────
function showPrivacyPolicy() {
  if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.parlance) {
    window.webkit.messageHandlers.parlance.postMessage('showPrivacyPolicy');
  }
}

// ── PROMPTS ──────────────────────────────────────────────────────
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
}

// ── SENTENCES ────────────────────────────────────────────────────
let sentenceIdCounter = 0;

function addSentence(prefill = '') {
  const id = ++sentenceIdCounter;
  const sentence = { id, text: '', feedback: null, status: 'empty' };
  state.sentences.push(sentence);

  const area = document.getElementById('sentencesArea');
  const row = document.createElement('div');
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
  const ta = document.getElementById('ta-' + id);
  const text = ta.value;
  const sentence = state.sentences.find(s => s.id === id);
  if (!sentence) return;
  sentence.text = text;
  sentence.status = 'dirty';
  sentence.feedback = null;
  updateCounts();

  clearTimeout(state.debounceTimers[id]);
  if (text.trim().length > 5) {
    if (state.activeSentenceId === id) showAnalyzingState(id);
    state.debounceTimers[id] = setTimeout(() => {
      if (sentence.text.trim()) analyzeSentence(id);
    }, 1500);
  }
}

function onSentenceKeydown(e, id) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    const ta = document.getElementById('ta-' + id);
    const text = ta.value.trim();
    if (text) {
      clearTimeout(state.debounceTimers[id]);
      analyzeSentence(id);
    }
  }
}

function updateCounts() {
  const sentences = state.sentences.filter(s => s.text.trim());
  document.getElementById('sentenceCount').textContent =
    `${sentences.length} sentence${sentences.length !== 1 ? 's' : ''}`;
  const words = sentences.reduce((acc, s) => acc + s.text.trim().split(/\s+/).filter(Boolean).length, 0);
  document.getElementById('wordCount').textContent =
    `${words} word${words !== 1 ? 's' : ''}`;

  state.sentences.forEach((s, i) => {
    const num = document.querySelector(`#row-${s.id} .sentence-num`);
    if (num) num.textContent = i + 1;
  });
}

// ── ANALYSIS ─────────────────────────────────────────────────────
async function analyzeSentence(id) {
  const sentence = state.sentences.find(s => s.id === id);
  if (!sentence || !sentence.text.trim()) return;

  const ta = document.getElementById('ta-' + id);
  const statusEl = document.getElementById('status-' + id);
  ta.classList.add('analyzing');
  ta.classList.remove('has-error', 'is-great');
  statusEl.textContent = '⏳';

  if (state.activeSentenceId === id) showAnalyzingState(id);

  const level = document.getElementById('levelSelect').value;

  try {
    let parsed;

    if (parlanceConfig.onDeviceAvailable) {
      parsed = await requestOnDeviceAnalysis(
        sentence.text, state.currentLanguage, level
      );
      sentence.analysisSource = 'onDevice';
    } else {
      parsed = await analyzeViaCloud(sentence.text, level);
      sentence.analysisSource = 'cloud';
    }

    applyFeedback(id, sentence, parsed, ta, statusEl);
  } catch (err) {
    if (parlanceConfig.onDeviceAvailable && sentence.analysisSource !== 'cloud') {
      try {
        const parsed = await analyzeViaCloud(sentence.text, level);
        sentence.analysisSource = 'cloud';
        applyFeedback(id, sentence, parsed, ta, statusEl);
        return;
      } catch (_) { /* both failed */ }
    }
    ta.classList.remove('analyzing');
    statusEl.textContent = '';
    if (err.message === 'offline') {
      showToast("You're offline — feedback will be available when you reconnect.");
    } else {
      showToast('Could not analyze — check your connection.');
    }
    console.error(err);
  }
}

function applyFeedback(id, sentence, parsed, ta, statusEl) {
  sentence.feedback = parsed;
  sentence.status = parsed.status === 'Excellent' ? 'great' : 'error';
  ta.classList.remove('analyzing');
  ta.classList.toggle('is-great', sentence.status === 'great');
  ta.classList.toggle('has-error', sentence.status === 'error');
  statusEl.textContent = sentence.status === 'great' ? '✓' : '⚠';
  if (state.activeSentenceId === id) showFeedback(id);
}

async function analyzeViaCloud(text, level) {
  if (!state.isOnline) throw new Error('offline');

  const prompt = buildPrompt(text, level);
  let response;

  if (parlanceConfig.mode === 'proxy' && parlanceConfig.proxyURL) {
    response = await fetch(parlanceConfig.proxyURL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 1000,
        messages: [{ role: 'user', content: prompt }]
      })
    });
  } else {
    const apiKey = parlanceConfig.apiKey || '';
    if (!apiKey) throw new Error('No API key available.');
    response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 1000,
        messages: [{ role: 'user', content: prompt }]
      })
    });
  }

  if (!response.ok) throw new Error(`API error ${response.status}`);
  const data = await response.json();
  const raw = data.content?.find(b => b.type === 'text')?.text || '';
  return parseJSON(raw);
}

async function deepAnalysis(id) {
  const sentence = state.sentences.find(s => s.id === id);
  if (!sentence || !sentence.text.trim()) return;

  const ta = document.getElementById('ta-' + id);
  const statusEl = document.getElementById('status-' + id);
  ta.classList.add('analyzing');
  statusEl.textContent = '⏳';
  if (state.activeSentenceId === id) showAnalyzingState(id);

  const level = document.getElementById('levelSelect').value;

  try {
    const parsed = await analyzeViaCloud(sentence.text, level);
    sentence.feedback = parsed;
    sentence.analysisSource = 'cloud';
    sentence.deepAnalyzed = true;
    applyFeedback(id, sentence, parsed, ta, statusEl);
  } catch (err) {
    ta.classList.remove('analyzing');
    statusEl.textContent = '';
    showToast('Deep analysis failed — check your connection.');
    console.error(err);
  }
}

function buildPrompt(sentence, level) {
  const lang = currentLang();

  let levelGuidance, nextLabel, targetLabel;
  if (level === 'C2') {
    nextLabel = 'native-level polish';
    targetLabel = null;
    levelGuidance = `Focus on near-native precision, stylistic elegance, idiomatic naturalness, and register mastery for professional interpreting. Flag any residual Anglicisms, calques, or unnatural phrasing. Provide a next_level_alt in ${lang.coachRole} showing the most polished native-level phrasing. target_level_alt should be null. If Excellent, explain what makes it native-quality.`;
  } else if (level === 'C1') {
    nextLabel = 'C2';
    targetLabel = null;
    levelGuidance = `Focus on professional register, advanced word precision, and naturalness for interpreting. Flag Anglicisms (English sentence structures used in ${lang.coachRole}). Provide a next_level_alt in ${lang.coachRole} showing C2 native-mastery phrasing. target_level_alt should be null. If Excellent, explain specifically what makes it C1-quality.`;
  } else if (level === 'B2') {
    nextLabel = 'C1';
    targetLabel = 'C2';
    levelGuidance = `Focus on verb tense correctness (especially subjunctive vs indicative), gender/number agreement, and Anglicisms. Always provide a next_level_alt in ${lang.coachRole} showing C1 professional interpreter phrasing, and a target_level_alt in ${lang.coachRole} showing C2 native-level mastery. If Excellent, explain which B2-level rule was applied correctly.`;
  } else {
    nextLabel = 'B2';
    targetLabel = 'C1';
    levelGuidance = `Focus on basic verb tense correctness and gender agreement. Be encouraging and clear. Always provide a next_level_alt in ${lang.coachRole} showing a B2-level version with more complex structures, and a target_level_alt in ${lang.coachRole} showing C1 professional interpreter phrasing. If Excellent, explain why it works at B1 level.`;
  }

  const targetLine = targetLabel
    ? `"target_level_alt": "The same idea at ${targetLabel} level, written entirely in ${lang.coachRole} — NEVER in English",`
    : `"target_level_alt": null,`;

  return `You are a ${lang.coachRole} professor training interpreters. The user is at level ${level}.

${levelGuidance}

Analyze this sentence: "${sentence}"

Respond with ONLY a valid JSON object — no markdown, no explanation outside the JSON:

{
  "status": "Excellent" or "Needs Improvement",
  "grammar_rule": "The specific grammar rule tested or applied — always explain, even when correct",
  "explanation": "WHY the sentence is correct or incorrect at the ${level} level — be specific and actionable",
  "correction": null or "Corrected version written entirely in ${lang.coachRole} (only if Needs Improvement)",
  "next_level_alt": "The same idea at ${nextLabel} level, written entirely in ${lang.coachRole} — NEVER in English",
  ${targetLine}
  "tip": null or "A practical tip about register, Anglicisms, or word precision that helps the learner level up"
}

Rules:
- CRITICAL: next_level_alt and target_level_alt must ALWAYS be written in ${lang.coachRole}, never in English
- Always provide next_level_alt${targetLabel ? ' and target_level_alt' : ''} — they help learners see the range above them
- Always identify the grammar rule, even when correct
- Always explain WHY — be specific, not vague. Give the learner something concrete to work on
- Keep explanation and grammar_rule in English; all sentence examples (correction, next_level_alt, target_level_alt) in ${lang.coachRole}
- Be encouraging but honest — this is for someone training to become a professional interpreter`;
}

function parseJSON(text) {
  try {
    const clean = text.replace(/```json|```/g, '').trim();
    return JSON.parse(clean);
  } catch {
    return {
      status: 'Excellent',
      grammar_rule: 'Unable to parse feedback',
      explanation: 'I had trouble parsing the feedback. Your sentence looks reasonable — keep going!',
      correction: null,
      next_level_alt: null,
      target_level_alt: null,
      tip: null
    };
  }
}

// ── FEEDBACK DISPLAY ─────────────────────────────────────────────
function switchTab(tab, btn) {
  if (tab === 'guide') {
    openGuideOverlay();
    return;
  }
  document.querySelectorAll('.feedback-tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('feedbackInner').style.display = tab === 'feedback' ? 'flex' : 'none';
  document.getElementById('promptsInner').style.display = tab === 'prompts' ? 'flex' : 'none';
  document.getElementById('guideInner').style.display = 'none';
}

function showAnalyzingState(id) {
  const inner = document.getElementById('feedbackInner');
  const waiting = document.getElementById('waitingCard');
  if (waiting) waiting.style.display = 'none';
  inner.querySelectorAll('.feedback-card, .analyzing-card').forEach(el => el.remove());

  const card = document.createElement('div');
  card.className = 'analyzing-card';
  card.id = 'analyzing-card';
  card.innerHTML = `
    <div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
    <div class="analyzing-text">Analyzing your sentence…</div>
  `;
  inner.appendChild(card);
}

function showFeedback(id) {
  const sentence = state.sentences.find(s => s.id === id);
  if (!sentence) return;

  const inner = document.getElementById('feedbackInner');
  const waiting = document.getElementById('waitingCard');
  if (waiting) waiting.style.display = 'none';

  inner.querySelectorAll('.feedback-card, .analyzing-card').forEach(el => el.remove());

  if (!sentence.feedback) {
    if (sentence.text.trim()) showAnalyzingState(id);
    else if (waiting) waiting.style.display = 'block';
    return;
  }

  const fb = sentence.feedback;
  const isExcellent = fb.status === 'Excellent';
  const statusLabel = isExcellent ? 'Excellent' : 'Needs Work';
  const statusClass = isExcellent ? 'score-excellent' : 'score-needs-work';

  const card = document.createElement('div');
  card.className = 'feedback-card';

  const level = document.getElementById('levelSelect').value;
  const nextLabel = level === 'C2' ? 'Native Polish' : level === 'C1' ? 'C2 Mastery' : level === 'B2' ? 'C1 Professional' : 'B2 Version';
  const targetLabel = level === 'B1' ? 'C1 Professional' : level === 'B2' ? 'C2 Mastery' : null;

  let bodyHTML = '';
  bodyHTML += feedbackItem('rule', 'label-rule', '📐 Grammar Rule', fb.grammar_rule, null);
  bodyHTML += feedbackItem('explanation', 'label-explanation',
    isExcellent ? '✨ Why This Works' : '⚠ What Needs Work', fb.explanation, null);
  if (fb.correction) bodyHTML += feedbackItem('correction', 'label-correction', '✍ Correction', fb.correction, null);
  if (fb.next_level_alt) bodyHTML += feedbackItem('next', 'label-next', `🔼 ${nextLabel} Version`, fb.next_level_alt, null);
  if (fb.target_level_alt && targetLabel) bodyHTML += feedbackItem('target', 'label-target', `🎯 ${targetLabel} Version`, fb.target_level_alt, null);
  if (fb.tip) bodyHTML += feedbackItem('tip', 'label-tip', '💡 Tip', fb.tip, null);

  const sourceLabel = sentence.analysisSource === 'cloud' ? 'Claude' : 'On-Device';

  card.innerHTML = `
    <div class="feedback-card-header">
      <div class="feedback-sentence-ref">Sentence ${state.sentences.findIndex(s => s.id === id) + 1}</div>
      <div class="feedback-score ${statusClass}">${statusLabel}</div>
      <div class="feedback-source">${sourceLabel}</div>
    </div>
    <div class="feedback-original">"${sentence.text}"</div>
    <div class="feedback-body">${bodyHTML}</div>
  `;

  if (!sentence.deepAnalyzed && (parlanceConfig.apiKey || parlanceConfig.proxyURL)) {
    const deepBtn = document.createElement('div');
    deepBtn.className = 'deep-analysis-footer';
    const btnLabel = sentence.analysisSource === 'onDevice'
      ? 'Deep Analysis with Claude'
      : 'Re-analyze with Claude';
    const hintLabel = sentence.analysisSource === 'onDevice'
      ? 'Get more detailed interpreter-level feedback'
      : 'Get a fresh detailed analysis';
    deepBtn.innerHTML = `
      <button class="deep-analysis-btn" onclick="deepAnalysis(${id})">${btnLabel}</button>
      <div class="deep-analysis-hint">${hintLabel}</div>
    `;
    card.appendChild(deepBtn);
  }

  inner.appendChild(card);
  inner.scrollTop = 0;
}

function feedbackItem(type, labelClass, label, text, example) {
  return `
    <div class="feedback-item">
      <div class="feedback-item-label ${labelClass}">${label}</div>
      <div class="feedback-item-text">${text}</div>
      ${example ? `<div class="feedback-example">${example}</div>` : ''}
    </div>
  `;
}

// ── GUIDE OVERLAY ────────────────────────────────────────────────
function openGuideOverlay() {
  const lang = currentLang();
  const overlay = document.getElementById('guideOverlay');
  const frame = document.getElementById('guideFrame');

  if (!lang.guideFile) {
    showToast('Guide coming soon for this language.');
    return;
  }

  frame.src = lang.guideFile;
  overlay.style.display = 'block';
}

function closeGuideOverlay() {
  const overlay = document.getElementById('guideOverlay');
  const frame = document.getElementById('guideFrame');
  overlay.style.display = 'none';
  frame.src = '';
}

window.addEventListener('message', (e) => {
  if (e.data === 'closeGuide') closeGuideOverlay();
});

// ── SAVE / LOAD ──────────────────────────────────────────────────
function saveEntry() {
  const title = document.getElementById('entryTitle').value || 'Untitled Entry';
  const sentences = state.sentences.filter(s => s.text.trim());
  if (!sentences.length) { showToast('Write at least one sentence first.'); return; }

  const entry = {
    id: Date.now(),
    title,
    language: state.currentLanguage,
    date: new Date().toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' }),
    sentences: sentences.map(s => s.text),
  };

  state.savedEntries.unshift(entry);
  try { localStorage.setItem('parlance_entries', JSON.stringify(state.savedEntries)); } catch(e) {}

  renderPastEntries();
  showToast('Entry saved! ✓');
}

function loadSavedEntries() {
  try {
    // Migrate from old key
    const old = localStorage.getItem('parlance_entries_old');
    if (old && !localStorage.getItem('parlance_entries')) {
      localStorage.setItem('parlance_entries', old);
    }
    const saved = localStorage.getItem('parlance_entries');
    if (saved) {
      state.savedEntries = JSON.parse(saved);
      renderPastEntries();
    }
  } catch(e) {}
}

function renderPastEntries() {
  if (!state.savedEntries.length) return;
  const bar = document.getElementById('pastBar');
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

// ── ENTRY VIEWER ────────────────────────────────────────────────
function viewEntry(entry) {
  document.getElementById('entryViewerTitle').textContent = entry.title || 'Untitled Entry';
  const langName = entry.language === 'fr' ? 'Français' : 'Español';
  document.getElementById('entryViewerMeta').textContent = `${entry.date} · ${langName}`;

  const body = document.getElementById('entryViewerBody');
  body.innerHTML = '';
  (entry.sentences || []).forEach((text, i) => {
    const row = document.createElement('div');
    row.className = 'entry-viewer-sentence';
    row.innerHTML = `
      <div class="entry-viewer-num">${i + 1}</div>
      <div class="entry-viewer-text">${text}</div>
    `;
    body.appendChild(row);
  });

  const overlay = document.getElementById('entryOverlay');
  overlay.style.display = 'flex';
  overlay.onclick = (e) => { if (e.target === overlay) closeEntryViewer(); };
}

function closeEntryViewer() {
  document.getElementById('entryOverlay').style.display = 'none';
}

// ── UTILS ────────────────────────────────────────────────────────
function showToast(msg) {
  const t = document.getElementById('errorToast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3500);
}

// ── START ────────────────────────────────────────────────────────
init();
