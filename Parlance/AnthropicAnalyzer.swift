import Foundation

final class AnthropicAnalyzer: Sendable {

    static let shared = AnthropicAnalyzer()

    private let endpoint = URL(string: "https://api.anthropic.com/v1/messages")!

    func analyze(
        sentence: String,
        language: String,
        level: String,
        ragContext: String,
        apiKey: String,
        model: String
    ) async throws -> [String: Any] {
        guard !apiKey.isEmpty else {
            throw ExternalError.noAPIKey("Anthropic")
        }

        let langName     = language == "fr" ? "French" : "Spanish"
        let systemPrompt = ExternalAnalyzer.shared.buildSystemPromptPublic(
            langName: langName, level: level, ragContext: ragContext
        )
        let userMessage  = "Analyze this \(langName) sentence: \"\(sentence)\""

        let payload: [String: Any] = [
            "model":      model,
            "max_tokens": 1024,
            "system":     systemPrompt,
            "messages": [
                ["role": "user", "content": userMessage],
            ],
        ]

        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(apiKey, forHTTPHeaderField: "x-api-key")
        request.setValue("2023-06-01", forHTTPHeaderField: "anthropic-version")
        request.setValue("Parlance/1.0", forHTTPHeaderField: "User-Agent")
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)
        request.timeoutInterval = 30

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let http = response as? HTTPURLResponse else {
            throw ExternalError.invalidResponse
        }
        guard http.statusCode == 200 else {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw ExternalError.httpError(http.statusCode, body)
        }

        guard let json    = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let content = json["content"] as? [[String: Any]],
              let text    = content.first?["text"] as? String else {
            throw ExternalError.parseError
        }

        return try ExternalAnalyzer.shared.parseAndNormalize(text, sentence: sentence)
    }
}
