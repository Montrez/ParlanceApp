/** Format shared/standards/*.json for system prompts — keep in sync with training/coach_standard.py */
(function (root) {
  function standardPromptBlock(standard) {
    if (!standard || !standard.name) return '';
    const lines = [
      `=== ${String(standard.name).toUpperCase()} ===`,
      `Normative authority: ${standard.normative_authority || 'RAE'}`,
      `CEFR: ${standard.cefr_framework || 'MCER'}`,
      '',
      String(standard.role || '').trim(),
      '',
      'PRINCIPLES (you must know and apply these):',
    ];
    for (const p of standard.principles || []) {
      lines.push(`- ${p}`);
    }
    lines.push('', 'NON-NEGOTIABLE ERRORS (always Needs Improvement + full correction):');
    for (const e of standard.non_negotiable_errors || []) {
      lines.push(`- ${e}`);
    }
    if (standard.excellent_means) {
      lines.push('', `Excellent: ${standard.excellent_means}`);
    }
    if (standard.needs_improvement_means) {
      lines.push(`Needs Improvement: ${standard.needs_improvement_means}`);
    }
    if (standard.interpreter_register) {
      lines.push(`Register: ${standard.interpreter_register}`);
    }
    lines.push('');
    return lines.join('\n');
  }

  root.ParlanceCoachStandard = {
    standardPromptBlock,
    // Looks up the language's registry entry (PARLANCE_LANGUAGES, from languages.js,
    // loaded earlier) for the global variable name holding its standard, rather than
    // hardcoding an es/fr check here — add coachStandardGlobal to the registry to
    // support a new language instead of touching this function.
    forLang(lang) {
      const info = root.PARLANCE_LANGUAGES && root.PARLANCE_LANGUAGES[lang];
      const globalName = info && info.coachStandardGlobal;
      const standard = globalName ? root[globalName] : null;
      return standard ? standardPromptBlock(standard) : '';
    },
  };
})(typeof globalThis !== 'undefined' ? globalThis : this);
