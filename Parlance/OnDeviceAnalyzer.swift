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

    @Guide(description: "A simpler B1-level way to express the same idea in the target language")
    var b1Alternative: String?

    @Guide(description: "A polished C1 professional interpreter-level version in the target language")
    var c1Alternative: String?

    @Guide(description: "Extra tip about register, Anglicisms, or word precision")
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
        case "C1":
            levelGuidance = """
            The learner is at C1 level — focus on professional register, advanced word precision, \
            and naturalness for interpreting. Flag Anglicisms (e.g. using English sentence structures \
            in \(langName)) and suggest professional alternatives. \
            Provide a c1_alternative showing the most polished interpreter-level phrasing. \
            If the sentence is Excellent, explain specifically what makes it C1-quality.
            """
        case "B2":
            levelGuidance = """
            The learner is at B2 level — focus on verb tense correctness (especially subjunctive vs indicative), \
            gender/number agreement, and common Anglicisms. \
            Provide a b1_alternative if the sentence is overly complex for their level, \
            and a c1_alternative to show what professional interpreter phrasing looks like. \
            If the sentence is Excellent, explain which B2-level rule they applied correctly.
            """
        default:
            levelGuidance = """
            The learner is at B1 level — focus on basic verb tense correctness and gender agreement. \
            Be encouraging and clear in explanations. \
            Provide a b1_alternative showing a simpler way to express the idea if the sentence has errors, \
            and a c1_alternative to show the professional target they are working toward. \
            If the sentence is Excellent, explain why it works at the B1 level.
            """
        }

        let instructions = """
        You are a \(langName) professor training interpreters. \
        \(levelGuidance) \
        Always identify the specific grammar rule being used, even when the sentence is correct. \
        Always explain WHY the sentence is correct or incorrect. \
        Keep explanations in English; \(langName) examples in \(langName). \
        Be encouraging but honest.
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
        if let v = fb.b1Alternative { dict["b1_alternative"] = v }
        if let v = fb.c1Alternative { dict["c1_alternative"] = v }
        if let v = fb.tip { dict["tip"] = v }

        return dict
    }
}
#endif
