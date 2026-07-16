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
        let langName = LanguageRegistry.displayName(for: language)
        let systemPrompt = buildSystemPrompt(langName: langName, ragContext: ragContext)
        let userPrompt   = "Analyze this \(langName) sentence: \"\(sentence)\""

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

        return try parseAndNormalize(text, sentence: sentence, language: language, level: level)
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
        buildSystemPrompt(langName: langName, ragContext: ragContext)
    }

    private func buildSystemPrompt(langName: String, ragContext: String) -> String {
        let registerLabel = langName == "French" ? "tu/vous" : "tú/usted"
        let formalRegister = langName == "French" ? "vous" : "usted"
        let informalRegister = langName == "French" ? "tu" : "tú"

        var prompt = """
        You are a \(langName) professor training professional interpreters. Do NOT assume the learner picked a CEFR level.

        Evaluate verb tense and mood, gender/number agreement, register (\(registerLabel)), Anglicisms, and naturalness for professional interpreting.

        CEFR & COMPLEXITY:
        - assessed_level: A1–C2 ONLY if highly confident from specific structures in this sentence. When uncertain, omit and use complexity_note without a CEFR label.
        - complexity_note: 1–2 English sentences on vocabulary, syntax, subordination, and register — what makes this sentence simple or advanced. Always include when possible, even without assessed_level.
        - next_level_alt / target_level_alt: stronger rewrites; CEFR labels only when assessed_level is set.

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
        - Grammatically correct sentences are "Excellent" — but explanation must cite specific structures in the learner's words (not generic praise).
        - Only mark "Needs Improvement" when there is an actual grammar error — not a style preference.
        - Do NOT set assessed_level unless highly confident from specific structures in the sentence. When uncertain, omit and use complexity_note.
        - ALWAYS include complexity_note describing THIS sentence's structures.
        - next_level_alt MUST rewrite the sentence at a higher level — never copy the input verbatim.
        - ALL example sentences (correction, next_level_alt, target_level_alt) MUST be COMPLETE SENTENCES in \(langName), NEVER in English. Do NOT return short labels or descriptions — return full, natural sentences.
        - next_level_alt and target_level_alt must express the SAME idea as the original sentence rephrased with grammar and vocabulary appropriate for that CEFR level. Do NOT add new information or embellish.
        - NEVER use Chinese, Japanese, Korean, Cyrillic, or any non-Latin characters in \(langName) sentences. Use ONLY Latin alphabet characters with standard \(langName) diacritics.
        - grammar_rule, explanation, register, and tip must be in English.

        Respond with ONLY a valid JSON object (no markdown, no text outside the JSON, no <think> tags):
        {
          "assessed_level": "A1" | "A2" | "B1" | "B2" | "C1" | "C2" | null,
          "complexity_note": "1–2 English sentences on sentence complexity (vocabulary, syntax, subordination, register)",
          "status": "Excellent" or "Needs Improvement",
          "grammar_rule": "The specific grammar rule tested or applied — always explain, even when correct",
          "explanation": "WHY the sentence is correct or incorrect — be specific and actionable",
          "correction": null or "Corrected sentence in \(langName) (only if Needs Improvement)",
          "register": "Identify the register: formal (\(formalRegister)) or informal (\(informalRegister)), and whether appropriate for a professional interpreter",
          "next_level_alt": "COMPLETE SENTENCE in \(langName): same idea one CEFR level above assessed_level, or null if no assessed_level",
          "target_level_alt": "COMPLETE SENTENCE in \(langName): two levels above assessed_level, or null",
          "tip": "Practical tip with a complete \(langName) example sentence showing stronger phrasing"
        }
        """

        return prompt
    }

    // MARK: - Response parsing

    func parseAndNormalize(
        _ raw: String, sentence: String = "", language: String = "es", level: String = ""
    ) throws -> [String: Any] {
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

        return normalize(result, sentence: sentence, language: language, level: level)
    }

    func normalize(
        _ raw: [String: Any], sentence: String = "", language: String = "es", level: String = ""
    ) -> [String: Any] {
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
        if let assessed = Self.normalizeAssessedLevel(raw["assessed_level"] as? String
            ?? raw["assessedLevel"] as? String
            ?? raw["sentence_level"] as? String) {
            result["assessed_level"] = assessed
        }
        if let note = (raw["complexity_note"] as? String ?? raw["complexityNote"] as? String)?
            .trimmingCharacters(in: .whitespacesAndNewlines), !note.isEmpty {
            result["complexity_note"] = note
        }
        if !sentence.isEmpty {
            applyFeedbackSanitizer(sentence: sentence, language: language, level: level, feedback: &result)
        }
        return result
    }

    /// Cloud-path parity sanitizer (issue #31): CEFR plausibility + verbatim-alt stripping, plus
    /// hallucination detection, known-error regex repairs, and register-conflict repair — the
    /// same class of checks the on-device validator applies. Delegates to `FeedbackSanitizer` so
    /// the logic is not duplicated per provider. Shared by all cloud providers (Groq, DeepSeek,
    /// OpenRouter, OpenAI, Kimi, Anthropic, Gemini, Firebase-proxied).
    func applyFeedbackSanitizer(
        sentence: String, language: String = "es", level: String = "", feedback: inout [String: Any]
    ) {
        FeedbackSanitizer.sanitize(sentence: sentence, level: level, language: language, feedback: &feedback)
    }

    static func assessedLevelPlausible(sentence: String, level: String, language: String = "es") -> Bool {
        FeedbackSanitizer.assessedLevelPlausible(sentence: sentence, level: level, language: language)
    }

    static func normalizeAssessedLevel(_ raw: String?) -> String? {
        FeedbackSanitizer.normalizeAssessedLevel(raw)
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
