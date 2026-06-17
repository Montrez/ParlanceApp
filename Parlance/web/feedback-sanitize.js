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

  /**
   * Detect sentence fragments produced by SLMs.
   * The most common failure: "porque [det] [noun]" with no conjugated verb in the causal clause.
   */
  function isFragmentSentence(text, lang) {
    if (!text || lang !== 'es') return false;
    // Pattern: ends with a causal connector followed by a noun phrase but no verb
    if (/\b(porque|pues|ya que|puesto que)\s+(la|el|los|las|mi|tu|su|un|una)\s+\w+[.!?]?\s*$/i.test(text)) {
      return true;
    }
    // Broader check: extract the clause after any causal connector and verify it has a conjugated verb
    const causalMatch = text.match(/\b(?:porque|pues|ya\s+que|puesto\s+que)\s+(.+)/i);
    if (causalMatch) {
      const clause = causalMatch[1];
      const conjugated = /\b(fui|fue|es|está|esta|tengo|hay|quiero|necesito|soy|voy|estoy|tiene|hace|van|son|están|estan|llegué|llegue|podía|podia|tenía|tenia|era|hice|hizo|estuve|estuvo|quise|vine|dije|trabajo|vive|viven|tienen|sé|se)\b/i;
      if (!conjugated.test(clause)) return true;
    }
    return false;
  }

  /**
   * Validate an AI-generated alt sentence.
   * Returns null when the alt is a fragment or lacks any conjugated verb (very short/incomplete).
   * Otherwise returns the text unchanged.
   */
  function sanitizeAlt(text, lang) {
    if (!text) return null;
    if (isFragmentSentence(text, lang)) return null;
    if (lang === 'es') {
      const words = text.trim().split(/\s+/);
      if (words.length <= 5) {
        const conjugated = /\b(fui|fue|es|está|esta|tengo|hay|quiero|necesito|soy|voy|estoy|tiene|hace|van|son|están|estan|llegué|llegue|podía|podia|tenía|tenia|era|hice|hizo|estuve|estuvo|quise|vine|dije)\b/i;
        if (!conjugated.test(text)) return null;
      }
    }
    return text;
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

  /**
   * Infer the sentence's actual register from pronouns and verb forms.
   * Returns a canonical register string, or null when inconclusive.
   */
  function inferRegisterFromSentence(sentence, lang) {
    const norm = normalizeTextForCompare(sentence);

    if (lang === 'fr') {
      // Possessive/subject tu-forms
      const hasTu = /\b(tu |t |te |toi|ton |ta |tes |tiens|viens|fais|dis|vas|es |peux|veux|sais|dois|penses|aimes|parles|habites|prends|mets|sors)\b/.test(norm);
      const hasVous = /\b(vous|votre|vos)\b/.test(norm);
      if (hasTu && !hasVous) return 'informal (tu)';
      if (hasVous && !hasTu) return 'formal (vous)';
      return null;
    }

    // Spanish — voseo first (most specific)
    if (/\bvos\b/.test(norm) || /\b(sos|tenes|haces|podes|queres|venis)\b/.test(norm)) {
      return 'voseo (vos) — informal, regional (Argentina/Uruguay/Central America)';
    }

    // Informal tú: possessive "tu" before a noun, subject "tú", te/ti, or
    // 2nd-person singular informal verb forms that are unambiguous
    const hasTuInformal =
      /\btu\s+\w/.test(norm) ||             // possessive "tu <noun>"
      /\btu\b/.test(norm) ||                // standalone tú/tu
      /\b(te|ti)\b/.test(norm) ||           // object/reflexive
      /\b(tienes|eres|estas|fuiste|hiciste|sabes|puedes|quieres|hablas|vives|dices|vienes|oye)\b/.test(norm);

    const hasUsted = /\busted(es)?\b/.test(norm);

    if (hasTuInformal && !hasUsted) return 'informal (tú)';
    if (hasUsted && !hasTuInformal) return 'formal (usted)';
    return null;
  }

  /** Return true when a register string is vague meta-advice rather than a concrete label. */
  function registerIsVague(register) {
    if (!register || register.trim().length < 6) return true;
    const low = register.toLowerCase();
    // Meta-advice patterns are always vague — check these first regardless of label words
    if (/^note\b/.test(low) || /\bwhether\b/.test(low) || /^consider\b/.test(low)
        || /^check\b/.test(low) || /^identify\b/.test(low) || /^state\b/.test(low)) return true;
    // Must assert at least one concrete register label
    if (/\b(informal|formal|voseo|usted|vous)\b/.test(low) || /\bt[uú]\b/.test(low)) return false;
    return true;
  }

  /** Build a concrete register string from sentence inference + interpreter context note. */
  function buildRegisterNote(inferred, lang) {
    if (lang === 'fr') {
      if (inferred && inferred.includes('informal'))
        return 'informal (tu) — casual; use vous in clinical, legal, or formal interpreter settings.';
      if (inferred && inferred.includes('formal'))
        return 'formal (vous) — appropriate for professional interpreting contexts.';
      return 'Register not determined from this sentence — default to vous in clinical/legal settings.';
    }
    if (inferred && inferred.startsWith('voseo'))
      return inferred + '; use usted in formal/professional interpreter settings.';
    if (inferred && inferred.includes('informal'))
      return 'informal (tú) — casual; shift to usted in clinical, legal, or court interpreting.';
    if (inferred && inferred.includes('formal'))
      return 'formal (usted) — appropriate for professional interpreting contexts.';
    return 'Register not determined from this sentence — use usted in clinical/legal settings, tú for casual conversation.';
  }

  /**
   * Correct an AI-reported register string when:
   *   (a) sentence evidence contradicts it, OR
   *   (b) it is vague meta-advice rather than a concrete label.
   */
  function sanitizeRegister(sentence, aiRegister, lang) {
    if (!sentence || !aiRegister) return aiRegister;
    const inferred = inferRegisterFromSentence(sentence, lang);

    // Case A: register is vague meta-advice — replace with concrete note
    if (registerIsVague(aiRegister)) {
      return buildRegisterNote(inferred, lang);
    }

    // Case B: register is concrete but contradicts sentence evidence
    if (!inferred) return aiRegister;
    const regNorm = aiRegister.toLowerCase();

    if (lang === 'fr') {
      const aiSaysFormal   = /\bvous\b/.test(regNorm) || /\bformal\b/.test(regNorm);
      const aiSaysInformal = /\binformal\b/.test(regNorm) || /\btu\b/.test(regNorm);
      if (inferred === 'informal (tu)' && aiSaysFormal && !aiSaysInformal) return buildRegisterNote(inferred, lang);
      if (inferred === 'formal (vous)' && aiSaysInformal && !aiSaysFormal) return buildRegisterNote(inferred, lang);
      return aiRegister;
    }

    const aiSaysFormal   = /\busted(es)?\b/.test(regNorm) || /\bformal\b/.test(regNorm);
    const aiSaysInformal = /\binformal\b/.test(regNorm) || /\bt[uú]\b/.test(regNorm);
    const aiSaysVoseo    = /\bvos\b/.test(regNorm);

    if (inferred.startsWith('informal') && aiSaysFormal  && !aiSaysInformal) return buildRegisterNote(inferred, lang);
    if (inferred.startsWith('formal')   && aiSaysInformal && !aiSaysFormal)  return buildRegisterNote(inferred, lang);
    if (inferred.startsWith('voseo')    && !aiSaysVoseo)                     return buildRegisterNote(inferred, lang);
    return aiRegister;
  }

  // ── Tip sanitizer ─────────────────────────────────────────────────────────

  const _GENERIC_TIP_PHRASES = [
    'apply each grammar fix',
    'apply each fix',
    'keeping your original meaning',
    'keep your original meaning',
    'note whether',
    'consider whether',
    'check if',
    'fix each bullet',
    'tighten vocabulary',
    'prefer precise verbs',
    'apply the fixes above',
    'change only the word',
    'adjust one verb or noun only',
  ];

  function tipIsGeneric(tip) {
    if (!tip || tip.trim().length < 15) return true;
    const low = tip.toLowerCase();
    if (_GENERIC_TIP_PHRASES.some((p) => low.includes(p))) return true;
    // Tips under 60 chars with no target-language example (no «» or "e.g.") are too thin
    if (tip.trim().length < 60 && !/[«»]/.test(tip) && !/e\.g\./i.test(tip)) return true;
    return false;
  }

  /**
   * Synthesize a concrete tip with a target-language example sentence,
   * based on the grammar_rule text and detected register.
   */
  function synthesizeTip(sentence, grammarRule, lang, register) {
    const rule = (grammarRule || '').toLowerCase();
    const isInformal = register && /informal/.test(register);

    if (lang === 'fr') {
      if (/subjun|subjonctif/.test(rule))
        return 'After verbs of wish, doubt, or emotion, use the subjunctive. E.g. «Je veux que tu **viennes** demain.»';
      if (/question|ponctuation|inversion/.test(rule))
        return 'French questions need a space before «?» in formal writing. E.g. «Comment allez-vous ?» or «Est-ce que vous allez bien ?»';
      if (/si.claus|conditionnel/.test(rule))
        return 'Si-clauses take the imperfect, not the conditional: «Si j\'**avais** le temps, je viendrais.»';
      if (/negat|ne.*pas/.test(rule))
        return 'Written French requires «ne … pas». E.g. «Je **ne** sais **pas**» — never drop «ne» in formal corrections.';
      if (/accord|participe|agreement/.test(rule))
        return 'Past participle agrees with the subject when using être: «Elle est **allée**» not «elle est allé».';
      if (/accent/.test(rule))
        return 'Accents change meaning: «où» (where) vs «ou» (or); «à» (at) vs «a» (has). Always include them.';
      if (/registre|register|vous|tu\b/.test(rule))
        return 'Formal settings (medical, legal) require vous. E.g. «Comment vous sentez-vous aujourd\'hui, madame ?»';
      return 'Match tu/vous to the setting. E.g. «Comment **allez-vous** ?» (formal) or «Comment **vas-tu** ?» (informal).';
    }

    // Spanish
    if (/question|inverted|¿|punctuation/.test(rule))
      return isInformal
        ? 'Add «¿» at the start of every question. E.g. «**¿**Cómo estás, amigo?» (informal) or «**¿**Cómo está usted?» (formal).'
        : 'Add «¿» at the start of every question. E.g. «**¿**Cómo está usted hoy, señor?» — especially in formal interpreter settings.';
    if (/leísmo|direct object|acusativo/.test(rule))
      return 'Use lo/la for direct objects, not le. E.g. «**lo** echo de menos» (him) or «**la** echo de menos» (her).';
    if (/por.*para|para.*por/.test(rule))
      return 'Por = cause/duration; para = purpose/recipient. E.g. «Trabajo **para** el hospital» vs «Lo hago **por** necesidad».';
    if (/subjunctive|subjuntivo|que.*verb|espero que|quiero que/.test(rule))
      return 'After querer/esperar/necesitar que, use the subjunctive. E.g. «Quiero que el paciente **venga** mañana.»';
    if (/si.claus|conditional protasis|imperfect subjunctive/.test(rule))
      return 'Si-clauses: use imperfect subjunctive in the condition. E.g. «Si **tuviera** tiempo, iría.» — never conditional after si.';
    if (/ser.*estar|estar.*ser/.test(rule))
      return 'Ser = identity/scheduled events; estar = state/location. E.g. «La cita **es** a las 3» vs «El paciente **está** nervioso».';
    if (/accent|tilde|acento/.test(rule))
      return 'Accent marks are required and change meaning. E.g. «comí» (I ate) vs «comi» (incorrect); «él» (he) vs «el» (the).';
    if (/gender|agreement|concordancia|género/.test(rule))
      return 'Adjectives and articles must match the noun in gender and number. E.g. «muchas cosas», «los documentos importantes».';
    if (/preterite|imperfect|pretérito|imperfecto/.test(rule))
      return 'Preterite = completed action; imperfect = ongoing/habitual. E.g. «Trabajé ocho horas» vs «Trabajaba de noche».';
    if (/register|formal|usted|tú/.test(rule))
      return isInformal
        ? 'This sentence uses tú (informal). In clinical/legal interpreting, shift to usted: «¿**Cómo está usted** hoy?»'
        : 'Formal usted fits here. In casual contexts you may use tú: «¿Cómo **estás** hoy, amigo?»';
    // y-coordinated preterite sentence — suggest sequencing/subordination connectors
    if (/ y /i.test(sentence) && /\b(fui|fue|hice|hizo|estuve|estuvo|llegué|llegue|salí|sali|comí|comi|trabajé|trabaje)\b/i.test(sentence)) {
      const rawParts = sentence.replace(/[.!?]\s*$/, '').split(/ y /i);
      const left = rawParts[0].trim();
      const right = rawParts.slice(1).join(' y ').trim();
      if (left && right) {
        return `With «y» chains, add sequencing: e.g. «${left} y después ${right}.» or use subordination: «${left} antes de ir a ${right}.»`;
      }
    }
    if (grammarRule && grammarRule.length > 12)
      return `${grammarRule.charAt(0).toUpperCase() + grammarRule.slice(1)}. Apply this consistently when interpreting for precision.`;
    return isInformal
      ? 'In professional interpreting, shift to usted. E.g. «¿**Cómo está usted** hoy?»'
      : 'Verify question marks (¿…?) and accent marks — both are required in professional written Spanish.';
  }

  /** Replace a vague tip with a synthesized concrete one. */
  function sanitizeTip(sentence, tip, grammarRule, lang, register) {
    if (!tipIsGeneric(tip)) return tip;
    return synthesizeTip(sentence, grammarRule, lang, register);
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

  /** Apply shared coach rules (shared/coach-rules/*.json) — same layer for every provider. */
  function applyCoachRules(sentence, out, lang) {
    if (typeof ParlanceCoachRules !== 'undefined' && ParlanceCoachRules.mergeWithAI) {
      Object.assign(out, ParlanceCoachRules.mergeWithAI(sentence, out, lang));
    }
    if (out._coach_enhanced && !out.complexity_note) {
      const wc = sentence.trim().split(/\s+/).filter(Boolean).length;
      const inferredLevel = confidentAssessedLevel(sentence, lang);
      const levelLabel = inferredLevel || 'intermediate';
      out.complexity_note = `Sentence (${wc} words) — ${levelLabel} interpreter practice: agreement, prepositions, and clause structure.`;
    }
    if (out._coach_enhanced && !out.assessed_level) {
      const confident = confidentAssessedLevel(sentence, lang);
      if (confident) {
        out.assessed_level = confident;
      }
    }
    return out;
  }

  /** Sanitize provider JSON — strip bad CEFR, fill confident levels, drop verbatim alts. */
  function sanitizeFeedbackResult(sentence, result, language) {
    if (!result || typeof result !== 'object') return result;
    const out = { ...result };
    normalizeFeedbackFields(out);
    const lang = language === 'fr' ? 'fr' : 'es';
    if (sentence && (lang === 'es' || lang === 'fr')) {
      applyCoachRules(sentence, out, lang);
    }
    preserveInferredFields(out, sentence, lang);
    // Correct register when vague or sentence evidence contradicts the AI's report
    if (sentence) {
      out.register = sanitizeRegister(sentence, out.register || '', lang);
    }
    // Replace generic tip with a concrete grammar-rule-based tip
    if (sentence) {
      out.tip = sanitizeTip(sentence, out.tip, out.grammar_rule, lang, out.register);
    }
    const sentNorm = normalizeTextForCompare(sentence);
    let fragmentAltDetected = false;
    if (out.next_level_alt) {
      const sanitized = sanitizeAlt(out.next_level_alt, lang);
      if (sanitized === null) { fragmentAltDetected = true; delete out.next_level_alt; }
      else if (normalizeTextForCompare(out.next_level_alt) === sentNorm) { delete out.next_level_alt; }
    }
    if (out.target_level_alt) {
      const sanitized = sanitizeAlt(out.target_level_alt, lang);
      if (sanitized === null) { fragmentAltDetected = true; delete out.target_level_alt; }
      else if (normalizeTextForCompare(out.target_level_alt) === sentNorm) { delete out.target_level_alt; }
    }
    // If a fragment alt was stripped, the tip may still cite it — regenerate from the sentence
    if (fragmentAltDetected && sentence) {
      out.tip = synthesizeTip(sentence, out.grammar_rule, lang, out.register);
    }
    return out;
  }

  const api = {
    sanitizeFeedbackResult,
    applyCoachRules,
    coerceFeedbackText,
    normalizeFeedbackFields,
    assessedLevelPlausible,
    normalizeAssessedLevel,
    normalizeTextForCompare,
    preserveInferredFields,
    confidentAssessedLevel,
    inferRegisterFromSentence,
    sanitizeRegister,
    registerIsVague,
    tipIsGeneric,
    sanitizeTip,
    synthesizeTip,
    isFragmentSentence,
    sanitizeAlt,
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
  if (typeof root !== 'undefined') {
    root.ParlanceFeedbackSanitize = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : typeof window !== 'undefined' ? window : this);
