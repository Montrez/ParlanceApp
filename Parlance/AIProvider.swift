import Foundation
import Security

// MARK: - Provider enum

enum AIProvider: String, CaseIterable, Codable {
    case parlanceCoach = "parlance"
    case onDevice   = "onDevice"
    case groq       = "groq"
    case deepSeek   = "deepSeek"
    case gemini     = "gemini"
    case openRouter = "openRouter"
    case openAI     = "openAI"
    case anthropic  = "anthropic"
    case kimi       = "kimi"

    var displayName: String {
        switch self {
        case .parlanceCoach: return "Parlance Coach"
        case .onDevice:   return "On-Device (Apple Intelligence)"
        case .groq:       return "Groq"
        case .deepSeek:   return "DeepSeek"
        case .gemini:     return "Gemini (Google)"
        case .openRouter: return "OpenRouter"
        case .openAI:     return "OpenAI"
        case .anthropic:  return "Anthropic (Claude)"
        case .kimi:       return "Kimi (Moonshot)"
        }
    }

    var subtitle: String {
        switch self {
        case .parlanceCoach:
            if ParlanceSLMAnalyzer.isOnDeviceModelAvailable {
                return "Private · Fine-tuned on device"
            }
            return "Model not bundled in this build"
        case .onDevice:   return "Private · No internet required"
        case .groq:       return "Free · Very fast"
        case .deepSeek:   return "Free · DeepSeek V4"
        case .gemini:     return "Free · 1M tokens/day"
        case .openRouter: return "Free models · Multi-provider"
        case .openAI:     return "GPT-5 · Paid"
        case .anthropic:  return "Claude · Paid"
        case .kimi:       return "Kimi K2.6 · Paid"
        }
    }

    /// When signed in via Firebase, cloud keys are proxied server-side.
    func requiresKey(isSignedIn: Bool = false) -> Bool {
        switch self {
        case .onDevice, .parlanceCoach:
            return false
        default:
            if isSignedIn { return false }
            return true
        }
    }

    var requiresKey: Bool {
        requiresKey(isSignedIn: false)
    }

    /// When signed in with Firebase, cloud keys are held server-side.
    func requiresAPIKey(isSignedIn: Bool) -> Bool {
        guard requiresKey else { return false }
        return !isSignedIn
    }

    var keyURL: URL? {
        switch self {
        case .parlanceCoach, .onDevice: return nil
        case .groq:       return URL(string: "https://console.groq.com/keys")
        case .deepSeek:   return URL(string: "https://platform.deepseek.com/api_keys")
        case .gemini:     return URL(string: "https://aistudio.google.com/app/apikey")
        case .openRouter: return URL(string: "https://openrouter.ai/keys")
        case .openAI:     return URL(string: "https://platform.openai.com/api-keys")
        case .anthropic:  return URL(string: "https://console.anthropic.com/settings/keys")
        case .kimi:       return URL(string: "https://platform.moonshot.cn/console/api-keys")
        }
    }

    var models: [(id: String, name: String)] {
        switch self {
        case .parlanceCoach:
            var list: [(id: String, name: String)] = []
            if ParlanceSLMAnalyzer.isOnDeviceModelAvailable(language: "es") {
                list.append(("parlance-es", "Parlance Spanish (Qwen 0.5B)"))
            }
            if ParlanceSLMAnalyzer.isOnDeviceModelAvailable(language: "fr") {
                list.append(("parlance-fr", "Parlance French (Qwen 0.5B)"))
            }
            if list.isEmpty {
                list.append(("parlance-es", "Parlance Coach (not bundled)"))
            }
            return list
        case .onDevice:
            return [("system", "Apple Intelligence (default)")]
        case .groq:
            return [
                ("openai/gpt-oss-120b",       "GPT-OSS 120B (best)"),
                ("llama-3.3-70b-versatile",   "Llama 3.3 70B (versatile)"),
                ("llama-3.1-8b-instant",      "Llama 3.1 8B (fast)"),
            ]
        case .deepSeek:
            return [
                ("deepseek-v4-flash",  "DeepSeek V4 Flash (fast)"),
                ("deepseek-v4-pro",    "DeepSeek V4 Pro (best)"),
            ]
        case .gemini:
            return [
                ("gemini-2.5-flash",        "Gemini 2.5 Flash (stable)"),
                ("gemini-3-flash-preview",  "Gemini 3 Flash (best)"),
            ]
        case .openRouter:
            return [
                ("meta-llama/llama-3.3-70b-instruct:free", "Llama 3.3 70B (free)"),
                ("google/gemma-3-27b-it:free",             "Gemma 3 27B (free)"),
                ("qwen/qwen3-8b:free",                     "Qwen3 8B (free)"),
            ]
        case .openAI:
            return [
                ("gpt-5.4-nano",  "GPT-5.4 Nano (fast)"),
                ("gpt-5.4-mini",  "GPT-5.4 Mini (best)"),
                ("gpt-5.5",       "GPT-5.5 (premium)"),
            ]
        case .anthropic:
            return [
                ("claude-haiku-4-5",  "Claude Haiku 4.5 (fast)"),
                ("claude-sonnet-4-6", "Claude Sonnet 4.6 (best)"),
                ("claude-opus-4-7",   "Claude Opus 4.7 (premium)"),
            ]
        case .kimi:
            return [
                ("kimi-k2.5",  "Kimi K2.5 (multimodal)"),
                ("kimi-k2.6",  "Kimi K2.6 (best)"),
            ]
        }
    }

    var defaultModel: String {
        models.first?.id ?? "default"
    }
}

// MARK: - Settings storage

final class AIProviderSettings: @unchecked Sendable {

    static let shared = AIProviderSettings()
    private init() {}

    // MARK: Provider + model (UserDefaults — non-sensitive)

    var selectedProvider: AIProvider {
        get {
            let raw = UserDefaults.standard.string(forKey: "parlance_ai_provider")
                ?? defaultProviderId
            if raw == "parlance" { return .parlanceCoach }
            return AIProvider(rawValue: raw) ?? fallbackProvider
        }
        set { UserDefaults.standard.set(newValue.rawValue, forKey: "parlance_ai_provider") }
    }

    private var defaultProviderId: String {
        ParlanceSLMAnalyzer.isOnDeviceModelAvailable ? "parlance" : "groq"
    }

    private var fallbackProvider: AIProvider {
        ParlanceSLMAnalyzer.isOnDeviceModelAvailable ? .parlanceCoach : .groq
    }

    func model(for provider: AIProvider) -> String {
        let stored = UserDefaults.standard.string(forKey: "parlance_ai_model_\(provider.rawValue)")
        // A saved id outlives the model it names — providers retire them without
        // notice. Falling back to the current default beats sending a 404.
        if let stored, provider.models.contains(where: { $0.id == stored }) {
            return stored
        }
        return provider.defaultModel
    }

    func setModel(_ model: String, for provider: AIProvider) {
        UserDefaults.standard.set(model, forKey: "parlance_ai_model_\(provider.rawValue)")
    }

    // MARK: API keys (Keychain — sensitive)

    func apiKey(for provider: AIProvider) -> String {
        guard provider.requiresKey(isSignedIn: false) else { return "" }
        return KeychainHelper.load(key: keychainKey(provider)) ?? ""
    }

    func setAPIKey(_ key: String, for provider: AIProvider) {
        guard provider.requiresKey(isSignedIn: false) else { return }
        if key.isEmpty {
            KeychainHelper.delete(key: keychainKey(provider))
        } else {
            KeychainHelper.save(key: keychainKey(provider), value: key)
        }
    }

    var activeAPIKey: String { apiKey(for: selectedProvider) }
    var activeModel:  String { model(for: selectedProvider) }

    private func keychainKey(_ provider: AIProvider) -> String {
        "parlance_apikey_\(provider.rawValue)"
    }
}

// MARK: - Keychain helper

enum KeychainHelper {

    static func save(key: String, value: String) {
        let data = Data(value.utf8)
        let query: [CFString: Any] = [
            kSecClass:            kSecClassGenericPassword,
            kSecAttrAccount:      key,
            kSecAttrService:      "app.parlance",
            kSecValueData:        data,
            kSecAttrAccessible:   kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly,
        ]
        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
    }

    static func load(key: String) -> String? {
        let query: [CFString: Any] = [
            kSecClass:            kSecClassGenericPassword,
            kSecAttrAccount:      key,
            kSecAttrService:      "app.parlance",
            kSecReturnData:       true,
            kSecMatchLimit:       kSecMatchLimitOne,
        ]
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess, let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    static func delete(key: String) {
        let query: [CFString: Any] = [
            kSecClass:       kSecClassGenericPassword,
            kSecAttrAccount: key,
            kSecAttrService: "app.parlance",
        ]
        SecItemDelete(query as CFDictionary)
    }
}
