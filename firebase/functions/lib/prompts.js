/**
 * System prompt builder — ported from Parlance/web/journal.js (buildSystemPrompt).
 */

function buildSystemPrompt(langName, ragContext = "") {
  let registerLabel;
  let formalRegister;
  let informalRegister;
  let evaluateFocus;
  let exampleSentenceRule;

  if (langName === "French") {
    registerLabel = "tu/vous";
    formalRegister = "vous";
    informalRegister = "tu";
    evaluateFocus =
      "verb tense and mood, gender/number agreement, register (tu/vous), Anglicisms, and naturalness for professional interpreting";
    exampleSentenceRule = `ALL example sentences (correction, next_level_alt, target_level_alt) MUST be COMPLETE SENTENCES in ${langName}, NEVER in English. Do NOT return short labels or descriptions — return full, natural sentences.`;
  } else if (langName === "English") {
    registerLabel = "formal/informal (and US/UK/AU/CA variety)";
    formalRegister = "formal";
    informalRegister = "informal";
    evaluateFocus =
      "articles, tense aspect, conditionals, false cognates from Spanish/French, preposition calques, register, and naturalness for professional interpreting";
    exampleSentenceRule =
      "ALL example sentences (correction, next_level_alt, target_level_alt) MUST be COMPLETE SENTENCES in English (the practice language). Do NOT return Spanish or French for those fields. Do NOT return short labels — return full, natural sentences.";
  } else {
    registerLabel = "tú/usted";
    formalRegister = "usted";
    informalRegister = "tú";
    evaluateFocus =
      "verb tense and mood, gender/number agreement, register (tú/usted), Anglicisms, and naturalness for professional interpreting";
    exampleSentenceRule = `ALL example sentences (correction, next_level_alt, target_level_alt) MUST be COMPLETE SENTENCES in ${langName}, NEVER in English. Do NOT return short labels or descriptions — return full, natural sentences.`;
  }

  let prompt = `You are a ${langName} professor training professional interpreters. Do NOT assume the learner picked a CEFR level.

Evaluate ${evaluateFocus}.

CEFR & COMPLEXITY:
- assessed_level: A1–C2 ONLY if highly confident from specific structures in this sentence. When uncertain, omit and use complexity_note without a CEFR label.
- complexity_note: 1–2 English sentences on vocabulary, syntax, subordination, and register — what makes this sentence simple or advanced. Always include when possible, even without assessed_level.
- next_level_alt / target_level_alt: stronger rewrites; CEFR labels only when assessed_level is set.

`;

  if (ragContext && ragContext.length > 0) {
    prompt += `REFERENCE KNOWLEDGE (use these rules to verify accuracy):
${ragContext}

`;
  }

  prompt += `CRITICAL ACCURACY RULES:
- Do NOT invent grammatical errors. Only flag real, clear mistakes.
- Grammatically correct sentences are "Excellent" — but explanation must cite specific structures in the learner's words (not generic praise).
- Only mark "Needs Improvement" when there is an actual grammar error — not a style preference.
- Do NOT set assessed_level unless highly confident from specific structures in the sentence. When uncertain, omit and use complexity_note.
- ALWAYS include complexity_note describing THIS sentence's structures.
- next_level_alt MUST rewrite the sentence at a higher level — never copy the input verbatim.
- ${exampleSentenceRule}
- next_level_alt and target_level_alt must express the SAME idea as the original sentence rephrased with grammar and vocabulary appropriate for that CEFR level. Do NOT add new information or embellish.
- NEVER use Chinese, Japanese, Korean, Cyrillic, or any non-Latin characters in ${langName} sentences. Use ONLY Latin alphabet characters with standard ${langName} diacritics.
- grammar_rule, explanation, register, and tip must be in English (meta commentary), even when the practice language is English.

Respond with ONLY a valid JSON object (no markdown, no text outside the JSON, no <think> tags):
{
  "assessed_level": "A1" | "A2" | "B1" | "B2" | "C1" | "C2" | null,
  "complexity_note": "1–2 English sentences on sentence complexity (vocabulary, syntax, subordination, register)",
  "status": "Excellent" or "Needs Improvement",
  "grammar_rule": "The specific grammar rule tested or applied — always explain, even when correct",
  "explanation": "WHY the sentence is correct or incorrect — be specific and actionable",
  "correction": null or "Corrected sentence in ${langName} (only if Needs Improvement)",
  "register": "Identify the register: formal (${formalRegister}) or informal (${informalRegister}), and whether appropriate for a professional interpreter",
  "next_level_alt": "COMPLETE SENTENCE in ${langName}: same idea one CEFR level above assessed_level, or null if no assessed_level",
  "target_level_alt": "COMPLETE SENTENCE in ${langName}: two levels above assessed_level, or null",
  "tip": "Practical tip with a complete ${langName} example sentence showing stronger phrasing"
}
`;

  return prompt;
}

function buildUserMessage(langName, sentence) {
  return `Analyze this ${langName} sentence: "${sentence}"`;
}

function langNameFromCode(language) {
  if (language === "fr") return "French";
  if (language === "en") return "English";
  return "Spanish";
}

module.exports = {
  buildSystemPrompt,
  buildUserMessage,
  langNameFromCode,
};
