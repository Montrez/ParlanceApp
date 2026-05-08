import Foundation

/// Routes analysis requests to whichever AI provider the user has configured.
/// Falls back to Groq if on-device is selected but unavailable.
final class UnifiedAnalyzer: Sendable {

    static let shared = UnifiedAnalyzer()

    func analyze(
        sentence: String,
        language: String,
        level: String,
        ragContext: String
    ) async throws -> [String: Any] {
        let settings = AIProviderSettings.shared
        var provider = settings.selectedProvider
        let model    = settings.model(for: provider)
        let apiKey   = settings.apiKey(for: provider)

        // On-device fallback: if unavailable, drop to next configured cloud provider
        if provider == .onDevice && !isOnDeviceAvailable {
            provider = firstAvailableCloudProvider() ?? .groq
        }

        switch provider {
        case .onDevice:
            return try await analyzeOnDevice(sentence: sentence, language: language, level: level)

        case .groq, .deepSeek, .openRouter, .openAI, .kimi:
            let resolvedKey = (provider == .groq && apiKey.isEmpty) ? Config.groqAPIKey : apiKey
            return try await ExternalAnalyzer.shared.analyze(
                sentence: sentence,
                language: language,
                level: level,
                ragContext: ragContext,
                provider: provider,
                apiKey: resolvedKey,
                model: model
            )

        case .anthropic:
            return try await AnthropicAnalyzer.shared.analyze(
                sentence: sentence,
                language: language,
                level: level,
                ragContext: ragContext,
                apiKey: apiKey,
                model: model
            )

        case .gemini:
            return try await GeminiAnalyzer.shared.analyze(
                sentence: sentence,
                language: language,
                level: level,
                ragContext: ragContext,
                apiKey: apiKey,
                model: model
            )
        }
    }

    var activeProviderName: String {
        var provider = AIProviderSettings.shared.selectedProvider
        if provider == .onDevice && !isOnDeviceAvailable {
            provider = firstAvailableCloudProvider() ?? .groq
        }
        return provider.displayName
    }

    // MARK: – On-device

    private var isOnDeviceAvailable: Bool {
        #if canImport(FoundationModels)
        if #available(iOS 26, *) { return OnDeviceAnalyzer.isAvailable }
        #endif
        return false
    }

    private func analyzeOnDevice(sentence: String, language: String, level: String) async throws -> [String: Any] {
        #if canImport(FoundationModels)
        if #available(iOS 26, *) {
            return try await OnDeviceAnalyzer().analyze(
                sentence: sentence, language: language, level: level
            )
        }
        #endif
        throw ExternalError.unsupportedProvider("On-Device (requires iOS 26+)")
    }

    // MARK: – Fallback

    private func firstAvailableCloudProvider() -> AIProvider? {
        let cloud: [AIProvider] = [.groq, .deepSeek, .gemini, .openRouter, .openAI, .anthropic, .kimi]
        return cloud.first { !AIProviderSettings.shared.apiKey(for: $0).isEmpty }
    }
}
