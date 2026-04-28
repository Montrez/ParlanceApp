import Foundation

final class GeminiAnalyzer: Sendable {

    static let shared = GeminiAnalyzer()

    func analyze(
        sentence: String,
        language: String,
        level: String,
        ragContext: String,
        apiKey: String,
        model: String
    ) async throws -> [String: Any] {
        guard !apiKey.isEmpty else {
            throw ExternalError.noAPIKey("Gemini")
        }

        let urlString = "https://generativelanguage.googleapis.com/v1beta/models/\(model):generateContent?key=\(apiKey)"
        guard let url = URL(string: urlString) else {
            throw ExternalError.invalidResponse
        }

        let langName     = language == "fr" ? "French" : "Spanish"
        let systemPrompt = ExternalAnalyzer.shared.buildSystemPromptPublic(
            langName: langName, level: level, ragContext: ragContext
        )
        let userMessage  = "Analyze this \(langName) sentence at \(level) level: \"\(sentence)\""

        let payload: [String: Any] = [
            "system_instruction": [
                "parts": [["text": systemPrompt]],
            ],
            "contents": [
                ["parts": [["text": userMessage]]],
            ],
            "generationConfig": [
                "temperature":      0.3,
                "maxOutputTokens":  1024,
                "responseMimeType": "application/json",
            ],
        ]

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
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

        guard let json        = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let candidates  = json["candidates"] as? [[String: Any]],
              let content     = candidates.first?["content"] as? [String: Any],
              let parts       = content["parts"] as? [[String: Any]],
              let text        = parts.first?["text"] as? String else {
            throw ExternalError.parseError
        }

        return try ExternalAnalyzer.shared.parseAndNormalize(text)
    }
}
