import Foundation

/// Handles any OpenAI-compatible chat completions API.
/// Used for: Groq, OpenAI, Kimi/Moonshot
final class ExternalAnalyzer: Sendable {

    static let shared = ExternalAnalyzer()

    func analyze(
        sentence: String,
        language: String,
        level: String,
        ragContext: String,
        provider: AIProvider,
        apiKey: String,
        model: String
    ) async throws -> [String: Any] {
        guard !apiKey.isEmpty else {
            throw ExternalError.noAPIKey(provider.displayName)
        }

        let endpoint = try endpointURL(for: provider)
        let langName = language == "fr" ? "French" : "Spanish"
        let systemPrompt = buildSystemPrompt(langName: langName, level: level, ragContext: ragContext)
        let userPrompt   = "Analyze this \(langName) sentence at \(level) level: \"\(sentence)\""

        let payload: [String: Any] = [
            "model": model,
            "messages": [
                ["role": "system", "content": systemPrompt],
                ["role": "user",   "content": userPrompt],
            ],
            "temperature": 0.3,
            "max_tokens": 1024,
            "response_format": ["type": "json_object"],
        ]

        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("Parlance/1.0", forHTTPHeaderField: "User-Agent")
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)
        request.timeoutInterval = 15

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let http = response as? HTTPURLResponse else {
            throw ExternalError.invalidResponse
        }
        guard http.statusCode == 200 else {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw ExternalError.httpError(http.statusCode, body)
        }

        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let choices = json["choices"] as? [[String: Any]],
              let content = choices.first?["message"] as? [String: Any],
              let text    = content["content"] as? String else {
            throw ExternalError.parseError
        }

        return try parseAndNormalize(text)
    }

    // MARK: - Provider endpoints

    private func endpointURL(for provider: AIProvider) throws -> URL {
        switch provider {
        case .groq:
            return URL(string: "https://api.groq.com/openai/v1/chat/completions")!
        case .deepSeek:
            return URL(string: "https://api.deepseek.com/chat/completions")!
        case .openRouter:
            return URL(string: "https://openrouter.ai/api/v1/chat/completions")!
        case .openAI:
            return URL(string: "https://api.openai.com/v1/chat/completions")!
        case .kimi:
            return URL(string: "https://api.moonshot.cn/v1/chat/completions")!
        default:
            throw ExternalError.unsupportedProvider(provider.displayName)
        }
    }

    // MARK: - Prompt

    /// Public alias so AnthropicAnalyzer and GeminiAnalyzer can share the same prompt.
    func buildSystemPromptPublic(langName: String, level: String, ragContext: String) -> String {
        buildSystemPrompt(langName: langName, level: level, ragContext: ragContext)
    }

    private func buildSystemPrompt(langName: String, level: String, ragContext: String) -> String {
        let registerLabel = langName == "French" ? "tu/vous" : "tú/usted"

        let nextLevel:    String
        let targetLevel:  String?
        let levelGuidance: String

        switch level.uppercased() {
        case "C2":
            nextLevel   = "native-polish"
            targetLevel = nil
            levelGuidance = """
            Focus on near-native precision, stylistic elegance, idiomatic naturalness, and register mastery \
            for professional interpreting. Flag any residual Anglicisms, calques, or unnatural phrasing. \
            Provide a next_level_alt showing the most polished native-level phrasing. \
            Identify the register used (\(registerLabel), formal/informal) and whether it is appropriate.
            """
        case "C1":
            nextLevel   = "C2"
            targetLevel = nil
            levelGuidance = """
            Focus on professional register, advanced word precision, and naturalness for interpreting. \
            Flag Anglicisms (English sentence structures used in \(langName)). \
            Provide a next_level_alt showing C2 native-mastery phrasing. \
            Identify the register (\(registerLabel)) and whether it matches a professional interpreting context.
            """
        case "B2":
            nextLevel   = "C1"
            targetLevel = "C2"
            levelGuidance = """
            Focus on verb tense correctness (especially subjunctive vs indicative), gender/number agreement, \
            and Anglicisms. Identify the register: is the sentence formal or informal? Would an interpreter \
            use this phrasing in a professional setting? Explain \(registerLabel) choice. \
            Provide next_level_alt (C1 professional interpreter phrasing) and target_level_alt (C2 native mastery).
            """
        case "B1":
            nextLevel   = "B2"
            targetLevel = "C1"
            levelGuidance = """
            Focus on basic verb tense correctness and gender agreement. Be encouraging and clear. \
            Identify the register: is the learner using \(registerLabel) appropriately? \
            Introduce the concept of formal vs informal register for interpreter training. \
            Provide next_level_alt (B2 with more complex structures) and target_level_alt (C1 professional interpreter phrasing).
            """
        case "A2":
            nextLevel   = "B1"
            targetLevel = "B2"
            levelGuidance = """
            Focus on basic present tense conjugation, gender agreement, and simple sentence structure. \
            Be encouraging. Check reflexive verbs, near future constructions, and basic vocabulary. \
            Gently introduce register awareness: note whether the sentence uses \(registerLabel) and explain why it matters \
            for someone training to become an interpreter. \
            Provide next_level_alt (B1 with past tenses) and target_level_alt (B2 complexity).
            """
        default: // A1
            nextLevel   = "A2"
            targetLevel = "B1"
            levelGuidance = """
            Focus on basic present tense, fundamental verb usage, and simple vocabulary. \
            Be very encouraging — this is an absolute beginner training to become an interpreter. \
            Check subject-verb agreement and basic word order. Gently note register: is the learner using \
            \(registerLabel)? Explain the difference simply and why interpreters must know both forms. \
            Provide next_level_alt (A2 with slightly more complex structures) and target_level_alt (B1 phrasing).
            """
        }

        let targetLine = targetLevel.map { "\"target_level_alt\": \"Same idea at \($0) level in \(langName)\"" }
            ?? "\"target_level_alt\": null"

        var prompt = """
        You are a \(langName) professor training professional interpreters. The learner is at CEFR level \(level).

        \(levelGuidance)

        """

        if !ragContext.isEmpty {
            prompt += """
            REFERENCE KNOWLEDGE (use these rules to verify accuracy):
            \(ragContext)

            """
        }

        prompt += """
        CRITICAL ACCURACY RULES:
        - Do NOT invent grammatical errors. Only flag real, clear mistakes.
        - A simple, grammatically correct sentence is "Excellent" even if it could be more sophisticated.
        - Only mark "Needs Improvement" when there is an actual grammar error — not a style preference.
        - ALL example sentences (correction, next_level_alt, target_level_alt) MUST be in \(langName), NEVER in English.
        - next_level_alt and target_level_alt must express ONLY the same idea as the original sentence — do NOT add new information, embellish, or invent extra content. Just rephrase the same meaning using grammar and vocabulary appropriate for that CEFR level.
        - NEVER use Chinese, Japanese, Korean, Cyrillic, or any non-Latin characters in \(langName) sentences. Use ONLY Latin alphabet characters with standard \(langName) diacritics.
        - grammar_rule, explanation, register, and tip must be in English.

        Respond with ONLY a valid JSON object (no markdown, no text outside the JSON, no <think> tags):
        {
          "status": "Excellent" or "Needs Improvement",
          "grammar_rule": "The specific grammar rule tested or applied — always explain, even when correct",
          "explanation": "WHY the sentence is correct or incorrect at the \(level) level — be specific and actionable",
          "correction": null or "Corrected sentence in \(langName) (only if Needs Improvement)",
          "register": "Identify the register: formal (\(langName == "French" ? "vous" : "usted")) or informal (\(langName == "French" ? "tu" : "tú")), and whether appropriate for a professional interpreter",
          "next_level_alt": "The SAME idea rephrased at \(nextLevel) level in \(langName) — same meaning, no added content",
          \(targetLine),
          "tip": "A practical tip about register, Anglicisms, or word precision for interpreter training"
        }
        """

        return prompt
    }

    // MARK: - Response parsing

    func parseAndNormalize(_ raw: String) throws -> [String: Any] {
        let cleaned = raw
            .replacingOccurrences(of: "<think>[\\s\\S]*?</think>", with: "", options: .regularExpression)
            .replacingOccurrences(of: "```json", with: "")
            .replacingOccurrences(of: "```",     with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)

        guard let start = cleaned.range(of: "{"),
              let end   = cleaned.range(of: "}", options: .backwards) else {
            throw ExternalError.parseError
        }

        let jsonString = String(cleaned[start.lowerBound..<end.upperBound])
        guard let data   = jsonString.data(using: .utf8),
              let result = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw ExternalError.parseError
        }

        return normalize(result)
    }

    func normalize(_ raw: [String: Any]) -> [String: Any] {
        var result: [String: Any] = [:]
        let status = raw["status"] as? String ?? "Excellent"
        result["status"]       = (status == "Excellent" || status == "Needs Improvement") ? status : "Excellent"
        result["grammar_rule"] = raw["grammar_rule"] as? String ?? "Grammar rule not identified"
        result["explanation"]  = raw["explanation"]  as? String ?? ""
        if let v = raw["correction"]       as? String { result["correction"]       = sanitizeLatin(v) }
        if let v = raw["register"]         as? String { result["register"]         = v }
        if let v = raw["next_level_alt"]   as? String { result["next_level_alt"]   = sanitizeLatin(v) }
        if let v = raw["target_level_alt"] as? String { result["target_level_alt"] = sanitizeLatin(v) }
        if let v = raw["tip"]              as? String { result["tip"]              = v }
        return result
    }

    private func sanitizeLatin(_ text: String) -> String {
        text.filter { ch in
            ch.isASCII || ch.unicodeScalars.allSatisfy { s in
                (0x00C0...0x024F).contains(s.value) ||  // Latin Extended (accents)
                (0x2000...0x206F).contains(s.value) ||  // General punctuation
                (0x00A0...0x00BF).contains(s.value)     // Latin-1 punctuation (¿, ¡, «, »)
            }
        }
    }
}

// MARK: - Errors

enum ExternalError: LocalizedError {
    case noAPIKey(String)
    case invalidResponse
    case httpError(Int, String)
    case parseError
    case unsupportedProvider(String)

    var errorDescription: String? {
        switch self {
        case .noAPIKey(let p):           return "No API key for \(p). Add one in AI Settings."
        case .invalidResponse:           return "Invalid response from API"
        case .httpError(let c, let b):   return "HTTP \(c): \(b.prefix(200))"
        case .parseError:                return "Could not parse AI response"
        case .unsupportedProvider(let p): return "\(p) is not supported in this context"
        }
    }
}
