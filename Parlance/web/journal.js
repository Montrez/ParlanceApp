// ── CONFIG (injected by Swift) ────────────────────────────────────
const parlanceConfig = window.__PARLANCE_CONFIG__ || { mode: 'direct', apiKey: '', proxyURL: '', onDeviceAvailable: false };

// ── GROQ BRIDGE ─────────────────────────────────────────────────
const pendingGroqRequests = {};
let groqRequestCounter = 0;

window.__parlanceGroqResult = function(requestId, result, error) {
  const pending = pendingGroqRequests[requestId];
  if (!pending) return;
  delete pendingGroqRequests[requestId];
  if (error) pending.reject(new Error(error));
  else pending.resolve(result);
};

function requestGroqAnalysis(sentence, language, level) {
  const ragContext = (typeof getRAGContext === 'function')
    ? getRAGContext(language, level, sentence)
    : '';

  return new Promise((resolve, reject) => {
    const requestId = 'groq_' + (++groqRequestCounter);
    pendingGroqRequests[requestId] = { resolve, reject };
    window.webkit.messageHandlers.parlance.postMessage({
      action: 'analyzeGroq',
      requestId, sentence, language, level, ragContext
    });
    setTimeout(() => {
      if (pendingGroqRequests[requestId]) {
        delete pendingGroqRequests[requestId];
        reject(new Error('Analysis timed out. Check your AI settings or connection.'));
      }
    }, 20000);
  });
}

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
        reject(new Error('On-device analysis timed out. Try again or switch to a cloud provider.'));
      }
    }, 20000);
  });
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
}

function updateThemeIcon() {
  const btn = document.getElementById('themeToggle');
  if (!btn) return;
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  btn.textContent = isDark ? '☾' : '☀';
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
      'Describe your first day learning Spanish.',
      'What does being an interpreter mean to you?',
      'Talk about a place you would like to visit in Spain or Latin America.',
      'Describe an important person in your life.',
      'What are your professional goals for this year?',
      'Write about a cultural tradition you find interesting.',
      'What do you think about the importance of languages in today\'s world?',
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
      'Describe your first day learning French.',
      'What does being an interpreter mean to you?',
      'Talk about a place you would like to visit in France or Francophone Africa.',
      'Describe an important person in your life.',
      'What are your professional goals for this year?',
      'Write about a cultural tradition you find interesting.',
      'What do you think about the importance of languages in today\'s world?',
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
  initTheme();
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

function showAISettings() {
  if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.parlance) {
    window.webkit.messageHandlers.parlance.postMessage('showAISettings');
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

  // Check offline cache first
  try {
    const cacheKey = 'parlance_analysis_cache';
    const cache = JSON.parse(localStorage.getItem(cacheKey) || '{}');
    const hash = btoa(unescape(encodeURIComponent(
      sentence.text + '|' + state.currentLanguage + '|' + level
    ))).slice(0, 40);
    if (cache[hash]) {
      sentence.analysisSource = (cache[hash].source || 'cached') + ' (cached)';
      applyFeedback(id, sentence, cache[hash].feedback, ta, statusEl);
      return;
    }
  } catch (_) {}

  try {
    // Route through the native Swift bridge which uses UnifiedAnalyzer
    const parsed = await requestGroqAnalysis(sentence.text, state.currentLanguage, level);
    sentence.analysisSource = parlanceConfig.activeProvider || 'AI';

    // Cache the result
    try {
      const cacheKey = 'parlance_analysis_cache';
      const cache = JSON.parse(localStorage.getItem(cacheKey) || '{}');
      const hash = btoa(unescape(encodeURIComponent(
        sentence.text + '|' + state.currentLanguage + '|' + level
      ))).slice(0, 40);
      cache[hash] = { feedback: parsed, source: sentence.analysisSource, ts: Date.now() };
      const keys = Object.keys(cache);
      if (keys.length > 200) {
        const sorted = keys.sort((a, b) => cache[a].ts - cache[b].ts);
        sorted.slice(0, keys.length - 200).forEach(k => delete cache[k]);
      }
      localStorage.setItem(cacheKey, JSON.stringify(cache));
    } catch (_) {}

    applyFeedback(id, sentence, parsed, ta, statusEl);
  } catch (err) {
    // Secondary fallback: on-device if native bridge fails
    if (parlanceConfig.onDeviceAvailable) {
      try {
        const parsed = await requestOnDeviceAnalysis(sentence.text, state.currentLanguage, level);
        sentence.analysisSource = 'On-Device';
        applyFeedback(id, sentence, parsed, ta, statusEl);
        return;
      } catch (_) { /* fallback also failed */ }
    }
    ta.classList.remove('analyzing');
    statusEl.textContent = '';
    showToast('Could not analyze — check AI settings or your connection.');
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

// buildPrompt is not used in the iOS web bridge (Swift builds the prompt natively),
// but kept as a reference for the prompt structure.

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
  const nextLabels = { C2: 'Native Polish', C1: 'C2 Mastery', B2: 'C1 Professional', B1: 'B2 Version', A2: 'B1 Version', A1: 'A2 Version' };
  const targetLabels = { B2: 'C2 Mastery', B1: 'C1 Professional', A2: 'B2 Version', A1: 'B1 Version' };
  const nextLabel = nextLabels[level] || 'Next Level';
  const targetLabel = targetLabels[level] || null;

  let bodyHTML = '';
  bodyHTML += feedbackItem('rule', 'label-rule', '📐 Grammar Rule', fb.grammar_rule, null);
  bodyHTML += feedbackItem('explanation', 'label-explanation',
    isExcellent ? '✨ Why This Works' : '⚠ What Needs Work', fb.explanation, null);
  if (fb.correction) bodyHTML += feedbackItem('correction', 'label-correction', '✍ Correction', fb.correction, null);
  if (fb.register) bodyHTML += feedbackItem('register', 'label-register', '🎭 Register', fb.register, null);
  if (fb.next_level_alt) bodyHTML += feedbackItem('next', 'label-next', `🔼 ${nextLabel} Version`, fb.next_level_alt, null);
  if (fb.target_level_alt && targetLabel) bodyHTML += feedbackItem('target', 'label-target', `🎯 ${targetLabel} Version`, fb.target_level_alt, null);
  if (fb.tip) bodyHTML += feedbackItem('tip', 'label-tip', '💡 Tip', fb.tip, null);

  const sourceLabel = sentence.analysisSource || parlanceConfig.activeProvider || 'AI';

  card.innerHTML = `
    <div class="feedback-card-header">
      <div class="feedback-sentence-ref">Sentence ${state.sentences.findIndex(s => s.id === id) + 1}</div>
      <div class="feedback-score ${statusClass}">${statusLabel}</div>
      <div class="feedback-source">${sourceLabel}</div>
    </div>
    <div class="feedback-original">"${sentence.text}"</div>
    <div class="feedback-body">${bodyHTML}</div>
  `;

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
    level: document.getElementById('levelSelect').value,
    date: new Date().toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' }),
    sentences: sentences.map(s => ({
      text: s.text,
      feedback: s.feedback || null,
      analysisSource: s.analysisSource || null,
    })),
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
  const levelLabel = entry.level ? ` · ${entry.level}` : '';
  document.getElementById('entryViewerMeta').textContent = `${entry.date} · ${langName}${levelLabel}`;

  const body = document.getElementById('entryViewerBody');
  body.innerHTML = '';

  const loadAllRow = document.createElement('div');
  loadAllRow.style.cssText = 'margin-bottom: 1rem; text-align: right;';
  const loadAllBtn = document.createElement('button');
  loadAllBtn.className = 'entry-load-btn';
  loadAllBtn.textContent = 'Load All to Editor';
  loadAllBtn.onclick = () => loadEntryToEditor(entry);
  loadAllRow.appendChild(loadAllBtn);
  body.appendChild(loadAllRow);

  (entry.sentences || []).forEach((s, i) => {
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
  if (entry.level) {
    document.getElementById('levelSelect').value = entry.level;
  }
  if (entry.title) {
    document.getElementById('entryTitle').value = entry.title;
  }
  const area = document.getElementById('sentencesArea');
  area.innerHTML = '';
  state.sentences = [];
  sentenceIdCounter = 0;
  (entry.sentences || []).forEach(s => {
    const text = typeof s === 'string' ? s : s.text;
    addSentence(text);
  });
  closeEntryViewer();
  switchTab('feedback', document.querySelector('.feedback-tab'));
  showToast('Entry loaded into editor.');
}

function deleteEntry(entryId) {
  const idx = state.savedEntries.findIndex(e => e.id === entryId);
  if (idx === -1) return;
  state.savedEntries.splice(idx, 1);
  try { localStorage.setItem('parlance_entries', JSON.stringify(state.savedEntries)); } catch(e) {}
  closeEntryViewer();
  renderPastEntries();
  if (!state.savedEntries.length) {
    document.getElementById('pastBar').style.display = 'none';
  }
  showToast('Entry deleted.');
}

function closeEntryViewer() {
  document.getElementById('entryOverlay').style.display = 'none';
}

// ── UTILS ────────────────────────────────────────────────────────
function escapeHTML(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function showToast(msg) {
  const t = document.getElementById('errorToast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3500);
}

// ── START ────────────────────────────────────────────────────────
init();
