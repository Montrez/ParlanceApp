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

  /** Sanitize provider JSON — strip bad CEFR, fill confident levels, drop verbatim alts. */
  function sanitizeFeedbackResult(sentence, result, language) {
    if (!result || typeof result !== 'object') return result;
    const out = { ...result };
    const lang = language === 'fr' ? 'fr' : 'es';
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
