import Foundation

/// Routes analysis requests to whichever AI provider the user has configured.
/// Signed-in users use Firebase `analyzeText` for cloud providers.
final class UnifiedAnalyzer: Sendable {

    static let shared = UnifiedAnalyzer()

    func analyze(
        sentence: String,
        language: String,
        level: String,
        ragContext: String,
        isSignedIn: Bool = false,
        webProviderId: String? = nil,
        webModel: String? = nil
    ) async throws -> [String: Any] {
        let settings = AIProviderSettings.shared
        var provider = settings.selectedProvider
        var model    = settings.model(for: provider)
        let apiKey   = settings.apiKey(for: provider)

        if let webProviderId,
           let mapped = FirebaseCloudAnalyzer.provider(fromWebId: webProviderId) {
            provider = mapped
            if let webModel, !webModel.isEmpty {
                model = webModel
            } else {
                model = settings.model(for: provider)
            }
        }

        if provider == .onDevice && !isOnDeviceAvailable {
            provider = firstAvailableCloudProvider(isSignedIn: isSignedIn) ?? .groq
            model = settings.model(for: provider)
        }

        if isSignedIn && provider.isCloudProvider {
            return try await FirebaseCloudAnalyzer.analyze(
                sentence: sentence,
                language: language,
                level: level,
                ragContext: ragContext,
                provider: provider,
                model: model
            )
        }

        switch provider {
        case .onDevice:
            return try await analyzeOnDevice(sentence: sentence, language: language, level: level)

        case .parlanceCoach:
            return try await ParlanceSLMAnalyzer.analyze(
                sentence: sentence, language: language, level: level, ragContext: ragContext
            )

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
            provider = firstAvailableCloudProvider(isSignedIn: false) ?? .groq
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

    private func firstAvailableCloudProvider(isSignedIn: Bool) -> AIProvider? {
        if isSignedIn {
            return .groq
        }
        let cloud: [AIProvider] = [.groq, .deepSeek, .gemini, .openRouter, .openAI, .anthropic, .kimi]
        return cloud.first { !AIProviderSettings.shared.apiKey(for: $0).isEmpty }
    }
}
