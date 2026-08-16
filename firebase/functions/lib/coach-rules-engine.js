/**
 * Parlance Coach Rules Engine — provider-agnostic Spanish/French grammar layer.
 * Rules live in shared/coach-rules/*.json (single source of truth).
 * Every AI provider runs model output through mergeWithAI() so feedback follows
 * the same patterns regardless of WebLLM, cloud API, Firebase, or on-device SLM.
 */
(function (root) {
  const RULES = { es: null, fr: null, en: null };
  const SUPPORTED_LANGS = new Set(['es', 'fr', 'en']);

  function normalizeTextForCompare(text) {
    return String(text || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^\w\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  /**
   * Whether a correction leaves the sentence untouched.
   *
   * Deliberately not normalizeTextForCompare(), which strips accents and
   * punctuation — the exact things an orthography fix adds. Judged by that,
   * "Hola, ¿dónde está?" looks identical to "Hola, donde esta?", so a correct
   * model answer reads as a no-op and gets thrown away.
   */
  function isVerbatimCorrection(sentence, correction) {
    const tidy = (t) => String(t || '').toLowerCase().replace(/\s+/g, ' ').trim();
    return tidy(sentence) === tidy(correction);
  }

  // Rule packs are shared with Python (re.sub, which reads \1 \2 as backreferences).
  // JS String.replace needs $1 $2 instead — normalize before replacing so both
  // runtimes honor the exact same "replace" string from shared/coach-rules/*.json.
  function toJsBackreferences(replace) {
    return String(replace == null ? '' : replace).replace(/\\(\d)/g, '$$$1');
  }

  function ruleMatches(text, rule) {
    const detect = rule.detect || {};
    const flags = detect.flags || 'i';
    if (detect.unless && text.includes(detect.unless)) return false;
    if (detect.unless_pattern) {
      try {
        if (new RegExp(detect.unless_pattern, flags).test(text)) return false;
      } catch (_) { /* ignore */ }
    }
    if (detect.require_pattern) {
      try {
        if (!new RegExp(detect.require_pattern, flags).test(text)) return false;
      } catch (_) { /* ignore */ }
    }
    if (detect.pattern) {
      try {
        return new RegExp(detect.pattern, flags).test(text);
      } catch (_) {
        return false;
      }
    }
    return false;
  }

  function detectFeminineTodoIssues(text, pack) {
    const issues = [];
    const nouns = pack.feminine_nouns || [];
    if (!nouns.length) return issues;

    const norm = normalizeTextForCompare(text);
    if (/\btoda\s+la\s+aplicaci/.test(norm)) return issues;

    const hasTodo = /\btodo\b/.test(norm);
    const hasFemNoun = nouns.some((n) => {
      const nn = normalizeTextForCompare(n);
      return norm.includes(nn);
    });
    if (!hasTodo || !hasFemNoun) return issues;
    if (/\btodo\s+la\s+aplicaci/.test(text) || /\btodo\s+por\s+la\s+aplicaci/.test(text)) {
      return issues;
    }
    if (/\baplicaci/.test(text) && /\btodo\b/.test(text) && !/\btoda\b/.test(text)) {
      issues.push({
        id: 'todo_before_feminine_noun',
        category: 'agreement',
        issue: '«Aplicación» is feminine — use «toda la aplicación», not «todo».',
        mention: ['toda la aplicación', 'feminine todo/toda'],
        grammar_rule: 'Gender agreement (todo/toda + feminine noun)',
      });
    }
    return issues;
  }

  function loadRules(lang) {
    const key = SUPPORTED_LANGS.has(lang) ? lang : 'es';
    if (RULES[key]) return RULES[key];
    const globalName = { es: 'ParlanceCoachRulesES', fr: 'ParlanceCoachRulesFR', en: 'ParlanceCoachRulesEN' }[key];
    if (globalName && root[globalName]) {
      RULES[key] = root[globalName];
      return RULES[key];
    }
    return null;
  }

  function detectIssues(text, lang) {
    const pack = loadRules(lang);
    if (!pack || !text) return [];

    const matched = [];
    const seen = new Set();
    const rules = [...(pack.rules || [])].sort((a, b) => (a.priority || 99) - (b.priority || 99));

    for (const rule of rules) {
      if (seen.has(rule.id)) continue;
      if (ruleMatches(text, rule)) {
        matched.push({
          id: rule.id,
          category: rule.category,
          issue: rule.issue,
          mention: rule.mention || [],
          grammar_rule: rule.grammar_rule,
        });
        seen.add(rule.id);
      }
    }

    for (const extra of detectFeminineTodoIssues(text, pack)) {
      if (!seen.has(extra.id)) {
        matched.push(extra);
        seen.add(extra.id);
      }
    }
    return matched;
  }

  function applyRepairs(text, lang) {
    const pack = loadRules(lang);
    if (!pack || !text) return String(text || '').trim();

    let c = String(text).trim();
    const rules = [...(pack.rules || [])].sort((a, b) => (a.priority || 99) - (b.priority || 99));

    for (const rule of rules) {
      if (!ruleMatches(c, rule)) continue;
      for (const step of rule.repair || []) {
        try {
          const flags = step.flags || 'gi';
          const re = new RegExp(step.pattern, flags);
          const replacement = toJsBackreferences(step.replace);
          c = c.replace(re, replacement);
        } catch (_) { /* ignore bad pattern */ }
      }
    }
    return c.replace(/\s+/g, ' ').trim();
  }

  const SHORT_CORRECTION_ALLOW_WORDS = new Set([
    // French function words / particles common in short corrections.
    'où', 'ou', 'à', 'a', 'là', 'la', 'du', 'des', 'de', "d'",
    "c'est", 'il est', 'elle est', 'ne', 'pas', 'que', 'qui',
    "j'ai", "j'aime", 'tu', 'vous', 'je', 'il', 'elle', 'on',
  ]);

  function isPlaceholderCorrection(text, lang) {
    if (!text || typeof text !== 'string') return true;
    const t = text.trim();
    const lower = t.toLowerCase().replace(/[.:]+$/, '');
    if (t.length < 15) {
      // Allow short but valid corrections (e.g. "j'aime", "où") for languages
      // with common short function-word fixes.
      if (lang === 'fr') return !SHORT_CORRECTION_ALLOW_WORDS.has(lower);
      return true;
    }
    const placeholders = ['corrected sentence', 'correction', 'n/a', 'null', 'none'];
    if (placeholders.includes(lower)) return true;
    if (/^(corrected|correction|fixed)\s*(sentence|version)?[.:]?$/i.test(t)) return true;
    if (lang === 'fr') {
      return !/[àâäéèêëîïôöùûüç]|(?:\b(le|la|les|un|une|que|qui|pour|par|est|il|elle|je|tu|vous|de|du|des|ne|pas)\b)/i.test(t);
    }
    if (lang === 'en') {
      // The target language IS English here, so (unlike ES/FR) real corrections look exactly
      // like the labels we're guarding against — only reject genuine placeholder phrasing
      // (already handled above), not "lacks accented/Spanish words".
      return false;
    }
    return !/[áéíóúñü]|(?:\b(el|la|los|las|que|por|para|tengo|tenemos|hacer|trabajo|aplicaci)\b)/i.test(t);
  }

  function correctionIsIncomplete(sentence, correction, lang) {
    if (!correction || isPlaceholderCorrection(correction, lang)) return true;
    const sent = normalizeTextForCompare(sentence);
    const corr = normalizeTextForCompare(correction);
    if (corr.length < sent.length * 0.6) return true;
    if (/aplicaci/.test(sent) && !/aplicaci/.test(corr)) return true;
    if (detectIssues(sentence, lang).some((i) => i.id === 'tenemos_que_tenamos') && /\btenamos\b/.test(corr)) return true;
    if (/\btodo\b/.test(sent) && /\baplicaci/.test(sent) && /\btodo\b/.test(corr) && !/\btoda\b/.test(corr)) return true;
    return false;
  }

  function explanationCoversIssue(explanation, issue) {
    const expl = String(explanation || '');
    const lower = expl.toLowerCase();
    if (issue.id === 'todo_toda' || issue.id === 'todo_before_feminine_noun' || issue.id === 'todo_por_la_aplicacion' || issue.id === 'todo_la_aplicacion') {
      if (/\btodo\s+la\s+aplicaci/i.test(expl) || /\btodo\s+por\s+la\s+aplicaci/i.test(expl)) return false;
      if (/\btenemos\s+todo\b/i.test(expl) && !/\btoda\b/i.test(expl)) return false;
      return /\btoda\s+la\s+aplicaci/i.test(expl)
        || (lower.includes('toda') && lower.includes('feminine') && lower.includes('aplic'));
    }
    if (issue.id && issue.id.startsWith('tenemos_que')) {
      if (/\btenamos\b/i.test(expl)) return false;
      return lower.includes('tenemos que');
    }
    return (issue.mention || []).some((m) => lower.includes(String(m).toLowerCase()));
  }

  function analyzeSentence(sentence, lang) {
    const issues = detectIssues(sentence, lang);
    const correction = applyRepairs(sentence, lang);
    const changed = correction.trim() !== String(sentence || '').trim();
    return {
      issues,
      correction: changed ? correction : null,
      hasErrors: issues.length > 0 || changed,
    };
  }

  /**
   * Merge rule-based ground truth with any AI provider JSON.
   * AI may add nuance; rules enforce non-negotiable Spanish patterns.
   */
  function mergeWithAI(sentence, aiFeedback, lang) {
    if (aiFeedback && aiFeedback._coach_repaired) return aiFeedback;
    const out = aiFeedback && typeof aiFeedback === 'object' ? { ...aiFeedback } : {};
    if (!SUPPORTED_LANGS.has(lang)) return out;

    const ground = analyzeSentence(sentence, lang);
    if (!ground.hasErrors) return out;

    const missed = ground.issues.filter((i) => !explanationCoversIssue(out.explanation, i));
    const built = ground.correction;
    const modelCorrBad = detectIssues(out.correction || '', lang).length > 0;
    const correctionWeak = !out.correction
      || isPlaceholderCorrection(out.correction, lang)
      || correctionIsIncomplete(sentence, out.correction, lang)
      || modelCorrBad
      || isVerbatimCorrection(sentence, out.correction);

    if (out.explanation) {
      out.explanation = applyRepairs(out.explanation, lang);
    }
    if (isPlaceholderCorrection(out.correction, lang)) {
      delete out.correction;
    }

    out.status = 'Needs Improvement';

    if (missed.length) {
      const bullets = missed.map((i) => `• ${i.issue}`).join('\n');
      const header = missed.length === ground.issues.length ? 'Issues in your sentence:' : 'Also fix:';
      out.explanation = out.explanation
        ? `${String(out.explanation).trim()}\n\n${header}\n${bullets}`
        : `${header}\n${bullets}`;
    }

    if (built && correctionWeak) {
      out.correction = built;
    } else if (out.correction && (modelCorrBad || correctionIsIncomplete(sentence, out.correction, lang))) {
      out.correction = applyRepairs(out.correction, lang);
      if (correctionIsIncomplete(sentence, out.correction, lang) && built) {
        out.correction = built;
      }
    }

    for (const key of ['next_level_alt', 'target_level_alt', 'tip']) {
      if (out[key] && detectIssues(out[key], lang).length > 0) {
        out[key] = applyRepairs(out[key], lang);
      }
    }

    const grammarRules = [...new Set(ground.issues.map((i) => i.grammar_rule).filter(Boolean))];
    if (!out.grammar_rule || String(out.grammar_rule).length < 20) {
      out.grammar_rule = grammarRules.length
        ? grammarRules.slice(0, 2).join('; ')
        : (loadRules(lang)?.grammar_rule_default || 'Spanish grammar');
    }

    out._coach_rules = ground.issues.map((i) => i.id);
    out._coach_enhanced = true;
    return out;
  }

  const api = {
    loadRules,
    detectIssues,
    applyRepairs,
    analyzeSentence,
    mergeWithAI,
    isPlaceholderCorrection,
    correctionIsIncomplete,
    normalizeTextForCompare,
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
  if (typeof root !== 'undefined') {
    root.ParlanceCoachRules = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : typeof window !== 'undefined' ? window : this);
