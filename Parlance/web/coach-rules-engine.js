/**
 * Parlance Coach Rules Engine — provider-agnostic Spanish/French grammar layer.
 * Rules live in shared/coach-rules/*.json (single source of truth).
 * Every AI provider runs model output through mergeWithAI() so feedback follows
 * the same patterns regardless of WebLLM, cloud API, Firebase, or on-device SLM.
 */
(function (root) {
  const RULES = { es: null, fr: null };

  function normalizeTextForCompare(text) {
    return String(text || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^\w\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
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
    const key = lang === 'fr' ? 'fr' : 'es';
    if (RULES[key]) return RULES[key];
    if (key === 'es' && root.ParlanceCoachRulesES) {
      RULES.es = root.ParlanceCoachRulesES;
      return RULES.es;
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
          c = step.once ? c.replace(re, step.replace) : c.replace(re, step.replace);
        } catch (_) { /* ignore bad pattern */ }
      }
    }
    return c.replace(/\s+/g, ' ').trim();
  }

  function isPlaceholderCorrection(text) {
    if (!text || typeof text !== 'string') return true;
    const t = text.trim();
    if (t.length < 15) return true;
    const lower = t.toLowerCase().replace(/[.:]+$/, '');
    const placeholders = ['corrected sentence', 'correction', 'n/a', 'null', 'none'];
    if (placeholders.includes(lower)) return true;
    if (/^(corrected|correction|fixed)\s*(sentence|version)?[.:]?$/i.test(t)) return true;
    return !/[áéíóúñü]|(?:\b(el|la|los|las|que|por|para|tengo|tenemos|hacer|trabajo|aplicaci)\b)/i.test(t);
  }

  function correctionIsIncomplete(sentence, correction, lang) {
    if (!correction || isPlaceholderCorrection(correction)) return true;
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
    const sentNorm = normalizeTextForCompare(sentence);
    const corrNorm = normalizeTextForCompare(correction);
    return {
      issues,
      correction: corrNorm !== sentNorm ? correction : null,
      hasErrors: issues.length > 0 || corrNorm !== sentNorm,
    };
  }

  /**
   * Merge rule-based ground truth with any AI provider JSON.
   * AI may add nuance; rules enforce non-negotiable Spanish patterns.
   */
  function mergeWithAI(sentence, aiFeedback, lang) {
    const out = aiFeedback && typeof aiFeedback === 'object' ? { ...aiFeedback } : {};
    if (lang !== 'es' && lang !== 'fr') return out;

    const ground = analyzeSentence(sentence, lang);
    if (!ground.hasErrors) return out;

    const missed = ground.issues.filter((i) => !explanationCoversIssue(out.explanation, i));
    const built = ground.correction;
    const sentNorm = normalizeTextForCompare(sentence);
    const modelCorrBad = detectIssues(out.correction || '', lang).length > 0;
    const correctionWeak = !out.correction
      || isPlaceholderCorrection(out.correction)
      || correctionIsIncomplete(sentence, out.correction, lang)
      || modelCorrBad
      || normalizeTextForCompare(out.correction) === sentNorm;

    if (out.explanation) {
      out.explanation = applyRepairs(out.explanation, lang);
    }
    if (isPlaceholderCorrection(out.correction)) {
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
