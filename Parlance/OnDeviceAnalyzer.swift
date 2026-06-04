import Foundation

#if canImport(FoundationModels)
import FoundationModels

@available(iOS 26, *)
@Generable(description: "Grammar feedback for a sentence. All example sentences must be in the same language as the input sentence.")
struct SentenceReview {
    @Guide(description: "CEFR level A1–C2 only if confident; omit or empty if unclear")
    var assessedLevel: String?

    @Guide(description: "1–2 English sentences on vocabulary, syntax, subordination, and register complexity")
    var complexityNote: String?

    @Guide(description: "Either 'Excellent' if grammatically correct, or 'Needs Improvement' only if there is a real error")
    var status: String

    @Guide(description: "The grammar rule being used in this sentence, in English. Always provided even when the sentence is correct.")
    var grammarRule: String

    @Guide(description: "Why the sentence is correct or incorrect, in English. Be specific.")
    var explanation: String

    @Guide(description: "Corrected sentence in the SAME language as the input. Nil if the sentence is already correct.")
    var correction: String?

    @Guide(description: "The same idea rephrased at the next CEFR level up, in the SAME language as the input sentence. Same meaning only — do NOT add new information or embellish. Must NOT be in a different language.")
    var nextLevelAlt: String?

    @Guide(description: "The same idea rephrased two CEFR levels up, in the SAME language as the input sentence. Same meaning only — do NOT add new information. Nil if learner is at C1 or C2. Must NOT be in a different language.")
    var targetLevelAlt: String?

    @Guide(description: "Identify the register used: formal (usted/vous) or informal (tú/tu), and whether it is appropriate for a professional interpreter setting. In English.")
    var register: String?

    @Guide(description: "A short practical tip about register (formal vs informal) or word choice, in English. Always include register awareness for interpreter training.")
    var tip: String?
}

@available(iOS 26, *)
final class OnDeviceAnalyzer: Sendable {

    static var isAvailable: Bool {
        SystemLanguageModel.default.isAvailable
    }

    func analyze(sentence: String, language: String, level: String) async throws -> [String: Any] {
        let langName = language == "fr" ? "French" : "Spanish"

        let instructions = """
        You are a \(langName) grammar checker for interpreter training. Do NOT assume the learner picked a CEFR level.

        CEFR & COMPLEXITY: Set assessedLevel only if confident (omit if unclear). Always provide complexityNote when possible. \
        Include nextLevelAlt and targetLevelAlt only when assessedLevel is set.

        LANGUAGE RULE: The sentence is in \(langName). \
        All example sentences you write (nextLevelAlt, targetLevelAlt, correction) MUST be in \(langName). \
        \(language == "es" ? "Write ALL example sentences in SPANISH. Do NOT write French." : "Write ALL example sentences in FRENCH. Do NOT write Spanish.")

        ACCURACY RULE: Only mark a sentence as "Needs Improvement" if there is a real grammar error. \
        If the sentence is grammatically correct, mark it as "Excellent". \
        Do NOT invent errors. A simple correct sentence is still correct.

        For nextLevelAlt: rewrite the same idea one CEFR level above assessedLevel in \(langName).
        For targetLevelAlt: rewrite two levels above assessedLevel (nil if assessedLevel is C1 or C2).

        Identify the grammar rule being used. Explain why the sentence is correct or incorrect at the assessed level. \
        Always include a tip about register (formal vs informal) — the learner is training to become an interpreter. \
        Keep grammarRule and explanation in English.
        """

        let session = LanguageModelSession(instructions: instructions)
        let prompt = "Analyze this \(langName) sentence: \"\(sentence)\""
        let response = try await session.respond(to: prompt, generating: SentenceReview.self)
        let fb = response.content

        var dict: [String: Any] = [
            "status": fb.status,
            "grammar_rule": fb.grammarRule,
            "explanation": fb.explanation
        ]
        if let assessed = ExternalAnalyzer.normalizeAssessedLevel(fb.assessedLevel) {
            dict["assessed_level"] = assessed
        }
        if let note = fb.complexityNote?.trimmingCharacters(in: .whitespacesAndNewlines), !note.isEmpty {
            dict["complexity_note"] = note
        }
        if let v = fb.correction { dict["correction"] = v }
        if let v = fb.register { dict["register"] = v }
        if let v = fb.nextLevelAlt { dict["next_level_alt"] = v }
        if let v = fb.targetLevelAlt { dict["target_level_alt"] = v }
        if let v = fb.tip { dict["tip"] = v }

        ExternalAnalyzer.shared.applyFeedbackSanitizer(sentence: sentence, feedback: &dict)
        return dict
    }
}
#endif
