import Foundation

#if canImport(FoundationModels)
import FoundationModels

@available(iOS 26, *)
@Generable(description: "Grammar feedback for a sentence. All example sentences must be in the same language as the input sentence.")
struct SentenceReview {
    @Guide(description: "Either 'Excellent' if grammatically correct, or 'Needs Improvement' only if there is a real error")
    var status: String

    @Guide(description: "The grammar rule being used in this sentence, in English. Always provided even when the sentence is correct.")
    var grammarRule: String

    @Guide(description: "Why the sentence is correct or incorrect, in English. Be specific.")
    var explanation: String

    @Guide(description: "Corrected sentence in the SAME language as the input. Nil if the sentence is already correct.")
    var correction: String?

    @Guide(description: "The same idea rewritten at the next CEFR level up, in the SAME language as the input sentence. Must NOT be in a different language.")
    var nextLevelAlt: String?

    @Guide(description: "The same idea rewritten two CEFR levels up, in the SAME language as the input sentence. Nil if learner is at C1 or C2. Must NOT be in a different language.")
    var targetLevelAlt: String?

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

        let nextLevelName: String
        let targetLevelName: String?
        switch level.uppercased() {
        case "C2":  nextLevelName = "native-polish"; targetLevelName = nil
        case "C1":  nextLevelName = "C2";            targetLevelName = nil
        case "B2":  nextLevelName = "C1";            targetLevelName = "C2"
        case "B1":  nextLevelName = "B2";            targetLevelName = "C1"
        case "A2":  nextLevelName = "B1";            targetLevelName = "B2"
        default:    nextLevelName = "A2";            targetLevelName = "B1"
        }

        let targetInstruction: String
        if let target = targetLevelName {
            targetInstruction = "For targetLevelAlt: rewrite the sentence at \(target) level in \(langName)."
        } else {
            targetInstruction = "Set targetLevelAlt to nil."
        }

        let instructions = """
        You are a \(langName) grammar checker. The learner is at CEFR level \(level).

        LANGUAGE RULE: The sentence is in \(langName). \
        All example sentences you write (nextLevelAlt, targetLevelAlt, correction) MUST be in \(langName). \
        \(language == "es" ? "Write ALL example sentences in SPANISH. Do NOT write French." : "Write ALL example sentences in FRENCH. Do NOT write Spanish.")

        ACCURACY RULE: Only mark a sentence as "Needs Improvement" if there is a real grammar error. \
        If the sentence is grammatically correct, mark it as "Excellent". \
        Do NOT invent errors. A simple correct sentence is still correct.

        For nextLevelAlt: rewrite the sentence at \(nextLevelName) level in \(langName). \
        \(targetInstruction)

        Identify the grammar rule being used. Explain why the sentence is correct or incorrect. \
        Always include a tip about register (formal vs informal) — the learner is training to become an interpreter. \
        Keep grammarRule and explanation in English.
        """

        let session = LanguageModelSession(instructions: instructions)
        let prompt = "Is this \(langName) sentence correct? \"\(sentence)\""
        let response = try await session.respond(to: prompt, generating: SentenceReview.self)
        let fb = response.content

        var dict: [String: Any] = [
            "status": fb.status,
            "grammar_rule": fb.grammarRule,
            "explanation": fb.explanation
        ]
        if let v = fb.correction { dict["correction"] = v }
        if let v = fb.nextLevelAlt { dict["next_level_alt"] = v }
        if let v = fb.targetLevelAlt { dict["target_level_alt"] = v }
        if let v = fb.tip { dict["tip"] = v }

        return dict
    }
}
#endif
