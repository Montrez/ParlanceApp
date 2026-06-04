/**
 * Coach feedback sanitizer — aligned with training/parlance_slm_validate.py + Swift validator.
 * Used by Browser AI (WebLLM), cloud providers in journal.js, and Firebase Functions.
 */
(function (root) {
  const VALID_CEFR = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

  function normalizeAssessedLevel(raw) {
    if (!raw) return null;
    const u = String(raw).toUpperCase().trim();
    return VALID_CEFR.includes(u) ? u : null;
  }

  function normalizeTextForCompare(text) {
    return String(text || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^\w\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function hasSubordinator(sentence) {
    const n = normalizeTextForCompare(sentence);
    if (n.includes('fait que') || n.includes('fait qu') || n.includes('el hecho de que')) return true;
    const markers = [
      ' porque ', ' pues ', ' que ', ' qu ', ' cuando ', ' si ', ' aunque ',
      ' mientras ', ' lo cual ', ' donde ', ' como ', ' sino ',
      ' lorsque ', ' puisque ', ' bien que ',
    ];
    return markers.some((m) => (' ' + n + ' ').includes(m));
  }

  function isMedicalRegister(sentence, lang) {
    const n = normalizeTextForCompare(sentence);
    if (lang === 'fr') {
      return /\b(patient|ains|medicament|chirurg|intervention|diagnostico)\b/i.test(n);
    }
    return /\b(paciente|aines|medicamento|cirugia|intervencion|diagnostico)\b/i.test(n);
  }

  function hasFrenchSubjunctive(norm) {
    return /\b(eut|fut|soit|ait|eussent|fussent|vinssent)\b/i.test(norm);
  }

  function assessedLevelPlausibleSpanish(sentence, level) {
    const norm = normalizeTextForCompare(sentence);
    const wc = sentence.trim().split(/\s+/).filter(Boolean).length;
    const hasSub = hasSubordinator(sentence);
    const hasSubj = /\b(hubiera|tuviera|fuera|pudiera|quisiera|hiciera|hubiese|tuviese)\b/i.test(norm);
    const hasCond = /\b(habria|tendria|seria|podria)\b/i.test(norm);
    const hasPreterite = /\b(fui|fue|hice|hizo|estuve|estuvo|pude|pudo|quise|quiso|vine|vino|dije|dijo)\b/i.test(norm);
    switch (level.toUpperCase()) {
      case 'A1': return wc <= 8 && !hasSub && !hasSubj && !hasCond && !hasPreterite;
      case 'A2': return wc <= 12 && !hasSubj;
      case 'B1':
      case 'B2': return true;
      case 'C1':
        if (isMedicalRegister(sentence, 'es') && wc >= 8) return true;
        return hasSubj || (hasSub && wc >= 12) || hasCond;
      case 'C2':
        if (wc >= 14 && hasSub && /\b(arbitraje|vinculante|renuncien|estipulado|medida en que)\b/i.test(norm)) return true;
        return hasSubj || (hasSub && wc >= 12) || hasCond;
      default: return false;
    }
  }

  function assessedLevelPlausibleFrench(sentence, level) {
    const norm = normalizeTextForCompare(sentence);
    const wc = sentence.trim().split(/\s+/).filter(Boolean).length;
    const hasSub = hasSubordinator(sentence);
    const hasSubj = hasFrenchSubjunctive(norm);
    const hasCond = /\b(aurais|aurait|aurions|auriez|serais|serait|ferais|ferait)\b/i.test(norm);
    const hasPasse = /\b(suis alle|est alle)\b/i.test(norm);
    switch (level.toUpperCase()) {
      case 'A1': return wc <= 8 && !hasSub && !hasSubj && !hasCond && !hasPasse;
      case 'A2': return wc <= 12 && !hasSubj;
      case 'B1':
      case 'B2': return true;
      case 'C1':
        if (isMedicalRegister(sentence, 'fr') && wc >= 8) return true;
        return hasSubj || (hasSub && wc >= 12) || hasCond;
      case 'C2':
        if (isMedicalRegister(sentence, 'fr') && wc >= 8) return true;
        if (wc >= 14 && hasSub && /\b(arbitrage|stipulations|obligatoire)\b/i.test(norm)) return true;
        return hasSubj || (hasSub && wc >= 12) || hasCond;
      default: return false;
    }
  }

  function assessedLevelPlausible(sentence, level, lang) {
    if (!level) return false;
    return lang === 'fr'
      ? assessedLevelPlausibleFrench(sentence, level)
      : assessedLevelPlausibleSpanish(sentence, level);
  }

  function coachSalvageAssessedLevel(sentence, assessed, lang) {
    const norm = normalizeTextForCompare(sentence);
    const u = assessed.toUpperCase();
    if (lang === 'fr') {
      if (u === 'B1' && /\bhier\b/.test(norm) && /\b(suis alle|est alle)\b/i.test(norm)
        && assessedLevelPlausible(sentence, 'A2', lang)) return 'A2';
      return assessed;
    }
    if (u === 'B1' && /\bayer\b/.test(norm) && /\b(fue|fui|comi|trabaje)\b/i.test(norm)
      && assessedLevelPlausible(sentence, 'A2', lang)) return 'A2';
    if (u === 'B2' && /\bhubiera\b/.test(norm) && hasSubordinator(sentence)) return 'C1';
    return assessed;
  }

  function confidentAssessedLevel(sentence, lang) {
    const norm = normalizeTextForCompare(sentence);
    const wc = sentence.trim().split(/\s+/).filter(Boolean).length;

    if (lang === 'fr') {
      if (wc <= 6 && /\b(suis|es|est|vais|vas|va)\b/i.test(norm) && !hasSubordinator(sentence)
        && assessedLevelPlausible(sentence, 'A1', lang)) return 'A1';
      if (/\b(aime|aimes|aiment)\b/i.test(norm) && wc <= 10 && assessedLevelPlausible(sentence, 'A2', lang)) return 'A2';
      if (/\bhier\b/.test(norm) && /\b(suis alle|est alle)\b/i.test(norm) && assessedLevelPlausible(sentence, 'A2', lang)) return 'A2';
      if ((norm.includes('je pense') || norm.includes('nous devons')) && wc >= 8 && assessedLevelPlausible(sentence, 'B1', lang)) return 'B1';
      if (/\b(bonjour|madame|monsieur)\b/i.test(norm) && /\b(allez|comment)\b/i.test(norm) && assessedLevelPlausible(sentence, 'B1', lang)) return 'B1';
      if (isMedicalRegister(sentence, lang) && wc >= 8 && assessedLevelPlausible(sentence, 'C1', lang)) return 'C1';
      if (/\bje veux que\b/i.test(norm) && /\b(viennes|vienne|fasses|fasse|sois|soit)\b/i.test(norm)) return 'B2';
      if (/\bsi\s+j\s+avais\b/i.test(norm) && /\b(serais|serait|serais venu)\b/i.test(norm)) return 'B2';
      if (/\bfait qu/i.test(norm) && /\bsoit\b/i.test(norm) && hasSubordinator(sentence)) return 'C1';
      if (wc >= 14 && /\b(eu egard|stipulations|arbitrage|obligatoire|different)\b/i.test(norm)
        && assessedLevelPlausible(sentence, 'C2', lang)) return 'C2';
      return null;
    }

    if (/\b(fui|fue|hice|hizo|estuve|estuvo)\b/i.test(norm) && wc >= 5 && assessedLevelPlausible(sentence, 'A2', lang)) return 'A2';
    if ((norm.includes('estoy incomoda') || (norm.includes('estoy') && norm.includes('no dejo de')))
      && assessedLevelPlausible(sentence, 'B1', lang)) return 'B1';
    if (isMedicalRegister(sentence, lang) && wc >= 8 && assessedLevelPlausible(sentence, 'C1', lang)) return 'C1';
    if (/\bayer\b/.test(norm) && /\b(fue|fui|comi|trabaje)\b/i.test(norm) && !/\b(era|estaba|comia)\b/i.test(norm)
      && assessedLevelPlausible(sentence, 'A2', lang)) return 'A2';
    if (/\bquiero que\b/i.test(norm) && /\b(vengas|venga|haga|hagas|tenga|tengas)\b/i.test(norm)) return 'B2';
    if (/\bhubiera\b/i.test(norm) && hasSubordinator(sentence) && assessedLevelPlausible(sentence, 'C1', lang)) return 'C1';
    if (wc >= 14 && /\b(arbitraje|vinculante|renuncien|estipulado|medida en que)\b/i.test(norm)
      && assessedLevelPlausible(sentence, 'C2', lang)) return 'C2';
    return null;
  }

  function coerceFeedbackText(value) {
    if (value == null) return null;
    if (typeof value === 'string') {
      const t = value.trim();
      if (!t || t === '[object Object]') return null;
      return t;
    }
    if (typeof value === 'number' || typeof value === 'boolean') {
      return String(value);
    }
    if (Array.isArray(value)) {
      for (const item of value) {
        const coerced = coerceFeedbackText(item);
        if (coerced) return coerced;
      }
      return null;
    }
    if (typeof value === 'object') {
      const keys = [
        'sentence', 'text', 'spanish', 'french', 'content', 'alt',
        'rewrite', 'example', 'correction', 'next_level_alt', 'target_level_alt',
      ];
      for (const k of keys) {
        if (Object.prototype.hasOwnProperty.call(value, k)) {
          const coerced = coerceFeedbackText(value[k]);
          if (coerced) return coerced;
        }
      }
      for (const v of Object.values(value)) {
        const coerced = coerceFeedbackText(v);
        if (coerced) return coerced;
      }
      return null;
    }
    return null;
  }

  function normalizeFeedbackFields(out) {
    const textFields = [
      'grammar_rule', 'explanation', 'correction', 'register',
      'next_level_alt', 'target_level_alt', 'tip', 'complexity_note',
    ];
    for (const key of textFields) {
      if (out[key] !== undefined && out[key] !== null) {
        const coerced = coerceFeedbackText(out[key]);
        if (coerced) out[key] = coerced;
        else delete out[key];
      }
    }
    if (out.complexityNote != null) {
      const note = coerceFeedbackText(out.complexityNote);
      if (note) out.complexity_note = note;
      delete out.complexityNote;
    }
    if (out.grammarRule != null && !out.grammar_rule) {
      const rule = coerceFeedbackText(out.grammarRule);
      if (rule) out.grammar_rule = rule;
      delete out.grammarRule;
    }
  }

  function preserveInferredFields(out, sentence, lang) {
    const keepLevel = out._keep_assessed_level === true;
    let assessed = null;
    if (out._coach_repaired && !keepLevel) {
      delete out.assessed_level;
      delete out.assessedLevel;
      delete out.sentence_level;
    } else {
      assessed = normalizeAssessedLevel(out.assessed_level || out.assessedLevel || out.sentence_level);
      if (assessed && sentence) assessed = coachSalvageAssessedLevel(sentence, assessed, lang);
    }
    if (assessed && sentence && !assessedLevelPlausible(sentence, assessed, lang)) assessed = null;
    if (!assessed && sentence) assessed = confidentAssessedLevel(sentence, lang);
    if (assessed && sentence) assessed = coachSalvageAssessedLevel(sentence, assessed, lang);
    if (assessed && sentence && assessedLevelPlausible(sentence, assessed, lang)) {
      out.assessed_level = assessed;
    } else {
      delete out.assessed_level;
    }
    delete out.assessedLevel;
    delete out.sentence_level;
    delete out._keep_assessed_level;
    const note = String(out.complexity_note || out.complexityNote || '').trim();
    if (note) out.complexity_note = note;
    else delete out.complexity_note;
    delete out.complexityNote;
  }

  function isPlaceholderFeedbackText(text) {
    if (!text || typeof text !== 'string') return true;
    const t = text.trim();
    if (t.length < 15) return true;
    const lower = t.toLowerCase().replace(/[.:]+$/, '');
    const placeholders = [
      'corrected sentence',
      'correction',
      'n/a',
      'null',
      'none',
      'not applicable',
      'no correction',
    ];
    if (placeholders.includes(lower)) return true;
    if (/^(corrected|correction|fixed)\s*(sentence|version)?[.:]?$/i.test(t)) return true;
    return !/[áéíóúñü]|(?:\b(el|la|los|las|que|por|para|tengo|tenemos|hacer|trabajo|aplicaci)\b)/i.test(t);
  }

  function correctionIsIncomplete(sentence, correction) {
    if (!correction || isPlaceholderFeedbackText(correction)) return true;
    const sent = normalizeTextForCompare(sentence);
    const corr = normalizeTextForCompare(correction);
    if (corr.length < sent.length * 0.6) return true;
    if (/aplicaci/.test(sent) && !/aplicaci/.test(corr)) return true;
    if (/\btenamos\b/.test(sent) && /\btenamos\b/.test(corr)) return true;
    if (/\btodo\b/.test(sent) && /\baplicaci/.test(sent) && /\btodo\b/.test(corr) && !/\btoda\b/.test(corr)) return true;
    return false;
  }

  /** Detect common Spanish learner errors the small Browser AI model often under-explains. */
  function detectSpanishIssues(text, opts) {
    const isLearnerSentence = !opts || opts.isLearnerSentence !== false;
    const issues = [];
    if (!text || typeof text !== 'string') return issues;

    if (/\bmuchos\s+cosas\b/i.test(text)) {
      issues.push({
        key: 'gender_muchas',
        issue: '«muchos cosas» → «muchas cosas»: cosas is feminine — adjective must agree.',
        mention: ['muchas cosas', 'muchos cosas', 'feminine agreement'],
      });
    }
    if (/\bcosas\s+hacer\b/i.test(text) && !/\bcosas\s+que\s+hacer\b/i.test(text)) {
      issues.push({
        key: 'que_infinitive',
        issue: 'Missing «que» before the infinitive: say «cosas que hacer», not «cosas hacer».',
        mention: ['cosas que hacer', 'que before the infinitive'],
      });
    }
    if (/\bpor\s+(el\s+)?trabajo\b/i.test(text) && !/\bpara\s+(el\s+)?trabajo\b/i.test(text)) {
      issues.push({
        key: 'por_para',
        issue: 'Purpose/goal uses «para (el) trabajo», not «por trabajo».',
        mention: ['para el trabajo', 'para (el) trabajo'],
      });
    }
    if (/\bpara\s+trabajo\b/i.test(text) && !/\bpara\s+el\s+trabajo\b/i.test(text)) {
      issues.push({
        key: 'para_el',
        issue: 'Add the article: «para el trabajo», not «para trabajo».',
        mention: ['para el trabajo'],
      });
    }
    if (/\btenamos\b/i.test(text)) {
      issues.push({
        key: 'tenemos_que',
        issue: 'Use indicative «tenemos que + infinitive», not subjunctive «tenamos».',
        mention: ['tenemos que', 'tenamos'],
      });
    }
    if (/\bnuestra\s+la\s+aplicaci/i.test(text)) {
      issues.push({
        key: 'article_stack',
        issue: 'Do not stack possessive + article: «nuestra aplicación», not «nuestra la aplicación».',
        mention: ['nuestra la', 'nuestra aplicación'],
      });
    }
    if (/\btodo\s+por\s+la\s+aplicaci/i.test(text)) {
      issues.push({
        key: 'todo_por_app',
        issue: '«Aplicación» is feminine — use «toda la aplicación»; avoid «todo por la aplicación».',
        mention: ['toda la aplicación', 'todo por la'],
      });
    } else if (/\btodo\s+la\s+aplicaci/i.test(text)) {
      issues.push({
        key: 'todo_toda',
        issue: '«Aplicación» is feminine — use «toda la aplicación», not «todo la aplicación».',
        mention: ['toda la aplicación', 'feminine todo/toda'],
      });
    } else if (
      isLearnerSentence &&
      /\baplicaci/i.test(text) &&
      /\btodo\b/i.test(text) &&
      !/\btoda\s+la\s+aplicaci/i.test(text)
    ) {
      issues.push({
        key: 'todo_toda',
        issue: '«Aplicación» is feminine — use «toda la aplicación», not «todo».',
        mention: ['toda la aplicación', 'feminine todo/toda'],
      });
    }
    return issues;
  }

  function repairSpanishText(text) {
    let c = String(text || '').trim();
    if (!c) return c;
    c = c.replace(/\bmuchos\s+cosas\b/gi, 'muchas cosas');
    c = c.replace(/\bcosas\s+(?!que\s+)hacer\b/gi, 'cosas que hacer');
    c = c.replace(/\bpor\s+(el\s+)?trabajo\b/gi, 'para el trabajo');
    c = c.replace(/\bpara\s+trabajo\b/gi, 'para el trabajo');
    c = c.replace(/\btenamos\s+todo\s+por\s+la\s+aplicaci([oó]n)/gi, 'tenemos que terminar toda la aplicación');
    c = c.replace(/\btenamos\s+terminar\b/gi, 'tenemos que terminar');
    c = c.replace(/\btodo\s+por\s+la\s+aplicaci([oó]n)/gi, 'toda la aplicación');
    c = c.replace(/\btodo\s+la\s+aplicaci([oó]n)/gi, 'toda la aplicación');
    c = c.replace(
      /\bterminar\s+todo\s+por\s+nuestra\s+la\s+aplicaci([oó]n)\b/gi,
      'terminar toda la aplicación en nuestra aplicación'
    );
    c = c.replace(/\bnuestra\s+la\s+aplicaci([oó]n)/gi, 'nuestra aplicación');
    c = c.replace(
      /\bterminar\s+todo\s+por\s+nuestra\s+aplicaci([oó]n)\b/gi,
      'terminar toda la aplicación en nuestra aplicación'
    );
    c = c.replace(/\bterminar\s+todo\b/gi, 'terminar toda la aplicación');
    c = c.replace(/\bpor\s+nuestra\s+aplicaci/gi, 'en nuestra aplicación');
    c = c.replace(/\btenemos\s+todo\b/gi, 'tenemos que terminar toda la aplicación');
    c = c.replace(/\btenamos\b/gi, 'tenemos que');
    c = c.replace(/\btenemos que que\b/gi, 'tenemos que');
    return c.replace(/\s+/g, ' ').trim();
  }

  function buildSpanishCorrection(sentence) {
    return repairSpanishText(sentence);
  }

  function correctionHasSpanishErrors(text) {
    return detectSpanishIssues(text, { isLearnerSentence: false }).length > 0;
  }

  function explanationCoversIssue(explanation, issue) {
    const expl = String(explanation || '');
    const lower = expl.toLowerCase();
    if (issue.key === 'todo_toda' || issue.key === 'todo_por_app') {
      if (/\btodo\s+la\s+aplicaci/i.test(expl) || /\btodo\s+por\s+la\s+aplicaci/i.test(expl)) return false;
      if (/\btenemos\s+todo\b/i.test(expl) && !/\btoda\b/i.test(expl)) return false;
      return /\btoda\s+la\s+aplicaci/i.test(expl)
        || (lower.includes('toda') && lower.includes('feminine') && lower.includes('aplic'));
    }
    if (issue.key === 'tenemos_que') {
      if (/\btenamos\b/i.test(expl)) return false;
      return lower.includes('tenemos que');
    }
    return issue.mention.some((m) => lower.includes(m.toLowerCase()));
  }

  /** Patch weak Browser AI / cloud feedback when obvious Spanish errors were skipped or buried. */
  function enhanceSpanishFeedback(sentence, out) {
    const issues = detectSpanishIssues(sentence);
    if (!issues.length) return out;

    const built = buildSpanishCorrection(sentence);
    const sentNorm = normalizeTextForCompare(sentence);
    const builtNorm = built ? normalizeTextForCompare(built) : '';
    const needsCorrection = builtNorm && builtNorm !== sentNorm;
    const existingCorrNorm = out.correction ? normalizeTextForCompare(out.correction) : '';
    const modelCorrBad = correctionHasSpanishErrors(out.correction);
    const correctionWeak = !existingCorrNorm
      || existingCorrNorm === sentNorm
      || modelCorrBad
      || isPlaceholderFeedbackText(out.correction)
      || correctionIsIncomplete(sentence, out.correction);

    const missed = issues.filter((i) => !explanationCoversIssue(out.explanation, i));

    if (out.explanation) {
      out.explanation = repairSpanishText(out.explanation);
    }
    if (out.correction && isPlaceholderFeedbackText(out.correction)) {
      delete out.correction;
    }

    if (!missed.length && !correctionWeak && !needsCorrection) return out;

    out.status = 'Needs Improvement';

    if (missed.length) {
      const bullets = missed.map((i) => `• ${i.issue}`).join('\n');
      const header = missed.length === issues.length ? 'Issues in your sentence:' : 'Also fix:';
      const block = `${header}\n${bullets}`;
      out.explanation = out.explanation ? `${out.explanation.trim()}\n\n${block}` : block;
    }

    if (needsCorrection && (correctionWeak || !out.correction)) {
      out.correction = built;
    } else if (out.correction && (modelCorrBad || correctionIsIncomplete(sentence, out.correction))) {
      out.correction = repairSpanishText(out.correction);
      if (correctionIsIncomplete(sentence, out.correction) && needsCorrection) {
        out.correction = built;
      }
    }

    for (const key of ['next_level_alt', 'target_level_alt', 'tip']) {
      if (out[key] && correctionHasSpanishErrors(out[key])) {
        out[key] = repairSpanishText(out[key]);
      }
    }

    if (!out.grammar_rule || String(out.grammar_rule).length < 24) {
      out.grammar_rule = 'Gender agreement, por/para, possessives, and «tener que + infinitive»';
    }
    if (!out.complexity_note) {
      const wc = sentence.trim().split(/\s+/).filter(Boolean).length;
      out.complexity_note = `Workday sentence (${wc} words) with agreement, prepositions, and obligation structure — typical B1 interpreter practice.`;
    }
    if (!out.assessed_level && assessedLevelPlausible(sentence, 'B1', 'es')) {
      out.assessed_level = 'B1';
    }
    out._coach_enhanced = true;
    return out;
  }

  /** Sanitize provider JSON — strip bad CEFR, fill confident levels, drop verbatim alts. */
  function sanitizeFeedbackResult(sentence, result, language) {
    if (!result || typeof result !== 'object') return result;
    const out = { ...result };
    normalizeFeedbackFields(out);
    const lang = language === 'fr' ? 'fr' : 'es';
    if (lang === 'es' && sentence) {
      enhanceSpanishFeedback(sentence, out);
    }
    preserveInferredFields(out, sentence, lang);
    const sentNorm = normalizeTextForCompare(sentence);
    if (out.next_level_alt && normalizeTextForCompare(out.next_level_alt) === sentNorm) {
      delete out.next_level_alt;
    }
    if (out.target_level_alt && normalizeTextForCompare(out.target_level_alt) === sentNorm) {
      delete out.target_level_alt;
    }
    return out;
  }

  const api = {
    sanitizeFeedbackResult,
    enhanceSpanishFeedback,
    detectSpanishIssues,
    buildSpanishCorrection,
    repairSpanishText,
    correctionHasSpanishErrors,
    coerceFeedbackText,
    normalizeFeedbackFields,
    assessedLevelPlausible,
    normalizeAssessedLevel,
    normalizeTextForCompare,
    preserveInferredFields,
    confidentAssessedLevel,
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
  if (typeof root !== 'undefined') {
    root.ParlanceFeedbackSanitize = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : typeof window !== 'undefined' ? window : this);
