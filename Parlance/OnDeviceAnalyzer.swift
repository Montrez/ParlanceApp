import Foundation

#if canImport(FoundationModels)
import FoundationModels

@available(iOS 26, *)
@Generable(description: "Language feedback for a sentence written by a learner")
struct SentenceReview {
    @Guide(description: "Either 'Excellent' or 'Needs Improvement'")
    var status: String

    @Guide(description: "The specific grammar rule applied or tested in this sentence, explained in English. Always provided even when correct.")
    var grammarRule: String

    @Guide(description: "Why the sentence is correct or incorrect at the learner's level, explained in English")
    var explanation: String

    @Guide(description: "Corrected version in the target language, or nil if already correct")
    var correction: String?

    @Guide(description: "The same idea rephrased at one level above the learner's current CEFR level, written entirely in the target language (Spanish or French), never in English")
    var nextLevelAlt: String?

    @Guide(description: "The same idea rephrased at two levels above the learner's current CEFR level, written entirely in the target language (Spanish or French), never in English. Nil if the learner is already at C1 or C2.")
    var targetLevelAlt: String?

    @Guide(description: "A practical tip about register, Anglicisms, or word precision that helps the learner level up")
    var tip: String?
}

@available(iOS 26, *)
final class OnDeviceAnalyzer: Sendable {

    static var isAvailable: Bool {
        SystemLanguageModel.default.isAvailable
    }

    func analyze(sentence: String, language: String, level: String) async throws -> [String: Any] {
        let langName = language == "fr" ? "French" : "Spanish"

        let levelGuidance: String
        switch level.uppercased() {
        case "C2":
            levelGuidance = """
            The learner is at C2 level — focus on near-native precision, stylistic elegance, idiomatic naturalness, \
            and register mastery for professional interpreting. Flag any residual Anglicisms, calques, or unnatural phrasing. \
            Provide a next_level_alt in \(langName) showing the most polished native-level phrasing possible. \
            target_level_alt should be nil at this level. \
            If the sentence is Excellent, explain what makes it native-quality.
            """
        case "C1":
            levelGuidance = """
            The learner is at C1 level — focus on professional register, advanced word precision, \
            and naturalness for interpreting. Flag Anglicisms (e.g. using English sentence structures \
            in \(langName)) and suggest professional alternatives. \
            Provide a next_level_alt in \(langName) showing C2-level native mastery phrasing. \
            target_level_alt should be nil at this level. \
            If the sentence is Excellent, explain specifically what makes it C1-quality.
            """
        case "B2":
            levelGuidance = """
            The learner is at B2 level — focus on verb tense correctness (especially subjunctive vs indicative), \
            gender/number agreement, and common Anglicisms. \
            Always provide a next_level_alt in \(langName) showing a C1 professional interpreter-level version, \
            and a target_level_alt in \(langName) showing C2 native-level mastery. \
            If the sentence is Excellent, explain which B2-level rule they applied correctly.
            """
        default:
            levelGuidance = """
            The learner is at B1 level — focus on basic verb tense correctness and gender agreement. \
            Be encouraging and clear in explanations. \
            Always provide a next_level_alt in \(langName) showing a B2-level version with more complex structures, \
            and a target_level_alt in \(langName) showing C1 professional interpreter phrasing. \
            If the sentence is Excellent, explain why it works at the B1 level.
            """
        }

        let instructions = """
        You are a \(langName) professor training interpreters. \
        \(levelGuidance) \
        Always identify the specific grammar rule being used, even when the sentence is correct. \
        Always explain WHY the sentence is correct or incorrect — be specific and actionable. \
        IMPORTANT: All alternatives (b1_alternative, c1_alternative, correction) MUST be written entirely in \(langName). Never write them in English. \
        Keep explanations and grammar_rule in English. \
        Be encouraging but honest. Give the learner something concrete to improve on.
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
        if let v = fb.correction { dict["correction"] = v }
        if let v = fb.nextLevelAlt { dict["next_level_alt"] = v }
        if let v = fb.targetLevelAlt { dict["target_level_alt"] = v }
        if let v = fb.tip { dict["tip"] = v }

        return dict
    }
}
#endif
