/**
 * Response parsing — uses shared feedback-sanitize.js (aligned with parlance_slm_validate.py).
 */

require("./coach-rules-es");
require("./coach-rules-fr");
require("./coach-rules-engine");
const { sanitizeFeedbackResult } = require("./feedback-sanitize");

function sanitizeLatin(text) {
  return [...text]
    .filter((ch) => {
      const code = ch.codePointAt(0);
      if (code <= 0x7f) return true;
      return (
        (code >= 0x00c0 && code <= 0x024f) ||
        (code >= 0x2000 && code <= 0x206f) ||
        (code >= 0x00a0 && code <= 0x00bf)
      );
    })
    .join("");
}

function normalize(raw, sentence = "", language = "es") {
  const result = {};
  const status = typeof raw.status === "string" ? raw.status : "Excellent";
  result.status =
    status === "Excellent" || status === "Needs Improvement" ? status : "Excellent";
  result.grammar_rule =
    typeof raw.grammar_rule === "string" ? raw.grammar_rule : "Grammar rule not identified";
  result.explanation = typeof raw.explanation === "string" ? raw.explanation : "";

  if (typeof raw.correction === "string") {
    result.correction = sanitizeLatin(raw.correction);
  }
  if (typeof raw.register === "string") {
    result.register = raw.register;
  }
  if (typeof raw.next_level_alt === "string") {
    result.next_level_alt = sanitizeLatin(raw.next_level_alt);
  }
  if (typeof raw.target_level_alt === "string") {
    result.target_level_alt = sanitizeLatin(raw.target_level_alt);
  }
  if (typeof raw.tip === "string") {
    result.tip = raw.tip;
  }
  const assessed = raw.assessed_level || raw.assessedLevel || raw.sentence_level;
  if (typeof assessed === "string") {
    const u = assessed.toUpperCase().trim();
    if (["A1", "A2", "B1", "B2", "C1", "C2"].includes(u)) {
      result.assessed_level = u;
    }
  }
  const complexity = raw.complexity_note || raw.complexityNote;
  if (typeof complexity === "string" && complexity.trim()) {
    result.complexity_note = complexity.trim();
  }
  if (raw._coach_repaired) {
    result._coach_repaired = true;
  }
  if (raw._keep_assessed_level) {
    result._keep_assessed_level = true;
  }

  return sentence ? sanitizeFeedbackResult(sentence, result, language) : result;
}

function parseAndNormalize(raw, sentence = "", language = "es") {
  const cleaned = raw
    .replace(/<think>[\s\S]*?<\/redacted_thinking>/g, "")
    .replace(/```json/g, "")
    .replace(/```/g, "")
    .trim();

  const start = cleaned.indexOf("{");
  const end = cleaned.lastIndexOf("}");
  if (start === -1 || end === -1 || end <= start) {
    throw new Error("Could not parse AI response");
  }

  const jsonString = cleaned.slice(start, end + 1);
  let parsed;
  try {
    parsed = JSON.parse(jsonString);
  } catch {
    throw new Error("Could not parse AI response");
  }

  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Could not parse AI response");
  }

  return normalize(parsed, sentence, language);
}

module.exports = {
  parseAndNormalize,
  normalize,
  sanitizeLatin,
};
