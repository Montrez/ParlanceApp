import Foundation
import MLXLLM
import MLXLMCommon
import MLXLMTransformers

/// On-device inference for Parlance Coach (Spanish / French / English, MLX 4-bit).
actor ParlanceSLMEngine {

    static let shared = ParlanceSLMEngine()

    private var containers: [String: ModelContainer] = [:]
    private var loadedLanguage: String?

    func isModelAvailable(language: String) -> Bool {
        ParlanceSLMModelLocator.resolvedModelDirectory(language: language) != nil
    }

    func unload() {
        containers.removeAll()
        loadedLanguage = nil
    }

    private func loadContainer(language: String) async throws -> ModelContainer {
        if let loaded = loadedLanguage, let container = containers[loaded], loaded == language {
            return container
        }
        if loadedLanguage != language {
            containers.removeAll()
            loadedLanguage = nil
        }
        if let container = containers[language] {
            loadedLanguage = language
            return container
        }
        guard let directory = ParlanceSLMModelLocator.resolvedModelDirectory(language: language) else {
            throw ParlanceSLMError.modelMissing
        }
        let loaded = try await LLMModelFactory.shared.loadContainer(from: directory)
        containers[language] = loaded
        loadedLanguage = language
        return loaded
    }

    func analyze(sentence: String, language: String, level: String, ragContext: String = "") async throws -> sending [String: Any] {
        guard LanguageRegistry.onDeviceSupportedCodes.contains(language) else {
            throw ParlanceSLMError.unsupportedLanguage
        }

        let model = try await loadContainer(language: language)
        let (system, user) = Self.prompts(sentence: sentence, language: language, level: level, ragContext: ragContext)

        var params = GenerateParameters()
        params.temperature = 0
        params.maxTokens = 768

        let session = ChatSession(
            model,
            instructions: system,
            generateParameters: params
        )
        let raw = try await session.respond(to: user)
        let parsed: [String: Any]
        do {
            parsed = try Self.parseFeedback(raw)
        } catch {
            return ParlanceSLMFeedbackValidator.sanitize(
                sentence: sentence,
                feedback: ParlanceSLMFeedbackValidator.fallbackFeedback(
                    sentence: sentence, level: level, language: language
                ),
                level: level,
                language: language
            )
        }
        return ParlanceSLMFeedbackValidator.sanitize(
            sentence: sentence, feedback: parsed, level: level, language: language
        )
    }

    // MARK: - Prompts (match training/parlance_slm_infer.py)

    /// Prompt-builder pairs (system, user) keyed by language code. `analyze(...)` already
    /// guards on `LanguageRegistry.onDeviceSupportedCodes`, so adding a language here (plus
    /// the model + registry row) is the only control-flow change needed — no switch/fatalError.
    private static let promptProviders: [String: @Sendable (String, String, String) -> (String, String)] = [
        "es": { sentence, level, ragContext in
            (
                ParlanceSLMFeedbackValidator.spanishSystemPrompt(level: level, ragContext: ragContext),
                ParlanceSLMFeedbackValidator.spanishUserPrompt(sentence: sentence, level: level)
            )
        },
        "fr": { sentence, level, ragContext in
            (
                ParlanceSLMFeedbackValidator.frenchSystemPrompt(level: level, ragContext: ragContext),
                ParlanceSLMFeedbackValidator.frenchUserPrompt(sentence: sentence, level: level)
            )
        },
        "en": { sentence, level, ragContext in
            (
                ParlanceSLMFeedbackValidator.englishSystemPrompt(level: level, ragContext: ragContext),
                ParlanceSLMFeedbackValidator.englishUserPrompt(sentence: sentence, level: level)
            )
        },
    ]

    private static func prompts(sentence: String, language: String, level: String, ragContext: String = "") -> (String, String) {
        guard let provider = promptProviders[language] else {
            assertionFailure("ParlanceSLMEngine: no prompt provider registered for language '\(language)'")
            return promptProviders["es"]!(sentence, level, ragContext)
        }
        return provider(sentence, level, ragContext)
    }

    // MARK: - JSON parsing (match training/parlance_slm_infer.py)

    private static func parseFeedback(_ raw: String) throws -> [String: Any] {
        let cleaned = raw
            .replacingOccurrences(of: "```json", with: "")
            .replacingOccurrences(of: "```", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)

        guard let start = cleaned.firstIndex(of: "{") else {
            throw ParlanceSLMError.parseError
        }
        var depth = 0
        var end: String.Index?
        var idx = start
        while idx < cleaned.endIndex {
            let ch = cleaned[idx]
            if ch == "{" { depth += 1 }
            if ch == "}" {
                depth -= 1
                if depth == 0 {
                    end = idx
                    break
                }
            }
            idx = cleaned.index(after: idx)
        }
        guard let end else { throw ParlanceSLMError.parseError }

        var jsonSlice = String(cleaned[start...end])
        jsonSlice = jsonSlice.replacingOccurrences(
            of: #",\s*}"#, with: "}", options: .regularExpression
        )
        guard let data = jsonSlice.data(using: .utf8) else {
            throw ParlanceSLMError.parseError
        }
        let object: [String: Any]
        do {
            guard let parsed = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                throw ParlanceSLMError.parseError
            }
            object = parsed
        } catch {
            throw ParlanceSLMError.parseError
        }
        return normalizeFeedback(object)
    }

    private static func normalizeFeedback(_ raw: [String: Any]) -> [String: Any] {
        var status = raw["status"] as? String ?? "Excellent"
        if status != "Excellent" && status != "Needs Improvement" {
            status = "Excellent"
        }

        var out: [String: Any] = [
            "status": status,
            "grammar_rule": raw["grammar_rule"] ?? raw["grammarRule"] ?? "",
            "explanation": raw["explanation"] ?? "",
        ]

        for key in ["correction", "register", "next_level_alt", "target_level_alt", "tip", "assessed_level", "complexity_note"] {
            if let val = raw[key] as? String, !val.isEmpty {
                out[key] = val
            }
        }
        return out
    }
}
