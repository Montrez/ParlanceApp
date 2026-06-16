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
    forLang(lang) {
      if (lang === 'fr' && root.ParlanceCoachStandardFR) {
        return standardPromptBlock(root.ParlanceCoachStandardFR);
      }
      if (lang === 'es' && root.ParlanceCoachStandardES) {
        return standardPromptBlock(root.ParlanceCoachStandardES);
      }
      return '';
    },
  };
})(typeof globalThis !== 'undefined' ? globalThis : this);
