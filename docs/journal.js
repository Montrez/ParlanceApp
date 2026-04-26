// ── Parlance Web — journal + guides (no AI feedback) ──

// ── LANGUAGE DEFINITIONS ─────────────────────────────────────────
const languages = {
  es: {
    code: 'es',
    name: 'Espanol',
    placeholder: 'Escribe una oracion en espanol...',
    titlePlaceholder: 'Entry title... (e.g. Mi primer dia en Valencia)',
    guideFile: 'guide-es.html',
    prompts: [
      "Describe como fue tu primer dia aprendiendo espanol.",
      "Que significa ser interprete para ti?",
      "Habla sobre un lugar que te gustaria visitar en Espana o Latinoamerica.",
      "Describe a una persona importante en tu vida.",
      "Cuales son tus metas profesionales para este ano?",
      "Escribe sobre una tradicion cultural que te parece interesante.",
      "Que opinas sobre la importancia de los idiomas en el mundo actual?",
    ]
  },
  fr: {
    code: 'fr',
    name: 'Francais',
    placeholder: 'Ecrivez une phrase en francais...',
    titlePlaceholder: 'Entry title... (e.g. Mon premier jour a Paris)',
    guideFile: 'guide-fr.html',
    prompts: [
      "Decrivez votre premier jour d'apprentissage du francais.",
      "Que signifie etre interprete pour vous ?",
      "Parlez d'un endroit que vous aimeriez visiter en France ou en Afrique francophone.",
      "Decrivez une personne importante dans votre vie.",
      "Quels sont vos objectifs professionnels pour cette annee ?",
      "Ecrivez sur une tradition culturelle qui vous semble interessante.",
      "Que pensez-vous de l'importance des langues dans le monde actuel ?",
    ]
  }
};

// ── STATE ─────────────────────────────────────────────────────────
const state = {
  sentences: [],
  activeSentenceId: null,
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
  const overlay = document.getElementById('privacyOverlay');
  overlay.style.display = 'flex';
  overlay.onclick = (e) => { if (e.target === overlay) hidePrivacyPolicy(); };
}

function hidePrivacyPolicy() {
  document.getElementById('privacyOverlay').style.display = 'none';
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
  const sentence = { id, text: '' };
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
    </div>
  `;
  area.appendChild(row);

  const ta = row.querySelector('textarea');
  ta.addEventListener('input', () => onSentenceInput(id));
  ta.addEventListener('keydown', (e) => onSentenceKeydown(e, id));
  ta.addEventListener('focus', () => { state.activeSentenceId = id; });

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
  const sentence = state.sentences.find(s => s.id === id);
  if (!sentence) return;
  sentence.text = ta.value;
  updateCounts();
}

function onSentenceKeydown(e, id) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    const ta = document.getElementById('ta-' + id);
    if (ta.value.trim()) addSentence();
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

// ── TABS ─────────────────────────────────────────────────────────
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
  showToast('Entry saved!');
}

function loadSavedEntries() {
  try {
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
  const langName = entry.language === 'fr' ? 'Francais' : 'Espanol';
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
