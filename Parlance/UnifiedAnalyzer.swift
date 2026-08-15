import Foundation

/// On-device Parlance Coach is the only analyzer on the phones.
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
        try await ParlanceSLMAnalyzer.analyze(
            sentence: sentence, language: language, level: level, ragContext: ragContext
        )
    }

    var activeProviderName: String {
        AIProvider.parlanceCoach.displayName
    }
}
