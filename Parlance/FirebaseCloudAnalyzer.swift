import FirebaseFunctions
import Foundation

/// Proxies cloud AI analysis through the Firebase callable `analyzeText`.
enum FirebaseCloudAnalyzer {

    static func analyze(
        sentence: String,
        language: String,
        level: String,
        ragContext: String,
        provider: AIProvider,
        model: String
    ) async throws -> [String: Any] {
        _ = try await AuthManager.shared.refreshIDToken()

        let payload: [String: Any] = [
            "sentence": sentence,
            "language": language,
            "ragContext": ragContext,
            "provider": provider.webProviderId,
            "model": model,
        ]

        let callable = Functions.functions().httpsCallable("analyzeText")
        callable.timeoutInterval = 60

        let result = try await callable.call(payload)
        guard let data = result.data as? [String: Any] else {
            throw ExternalError.parseError
        }

        if let feedback = data["feedback"] as? [String: Any] {
            return ExternalAnalyzer.shared.normalize(feedback, sentence: sentence, language: language, level: level)
        }
        return ExternalAnalyzer.shared.normalize(data, sentence: sentence, language: language, level: level)
    }

    static func provider(fromWebId id: String) -> AIProvider? {
        switch id {
        case "groq":       return .groq
        case "deepseek":   return .deepSeek
        case "gemini":     return .gemini
        case "openrouter": return .openRouter
        case "openai":     return .openAI
        case "anthropic":  return .anthropic
        case "kimi":       return .kimi
        case "parlance":   return .parlanceCoach
        default:           return AIProvider(rawValue: id)
        }
    }
}

extension AIProvider {

    /// Journal.js provider id (localStorage).
    var webProviderId: String {
        switch self {
        case .deepSeek:   return "deepseek"
        case .openRouter: return "openrouter"
        case .openAI:     return "openai"
        default:          return rawValue
        }
    }

    var isCloudProvider: Bool {
        switch self {
        case .onDevice, .parlanceCoach: return false
        default: return true
        }
    }
}
