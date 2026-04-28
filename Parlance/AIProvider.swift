import Foundation
import Security

// MARK: - Provider enum

enum AIProvider: String, CaseIterable, Codable {
    case onDevice  = "onDevice"
    case groq      = "groq"
    case openAI    = "openAI"
    case anthropic = "anthropic"
    case gemini    = "gemini"
    case kimi      = "kimi"

    var displayName: String {
        switch self {
        case .onDevice:  return "On-Device (Apple Intelligence)"
        case .groq:      return "Groq"
        case .openAI:    return "OpenAI"
        case .anthropic: return "Anthropic (Claude)"
        case .gemini:    return "Gemini (Google)"
        case .kimi:      return "Kimi (Moonshot)"
        }
    }

    var subtitle: String {
        switch self {
        case .onDevice:  return "Private · No internet required"
        case .groq:      return "Fast · Free tier available"
        case .openAI:    return "GPT-4o · Paid"
        case .anthropic: return "Claude · Paid"
        case .gemini:    return "Google · Free tier available"
        case .kimi:      return "Moonshot AI · Paid"
        }
    }

    var requiresKey: Bool {
        self != .onDevice
    }

    var keyURL: URL? {
        switch self {
        case .onDevice:  return nil
        case .groq:      return URL(string: "https://console.groq.com/keys")
        case .openAI:    return URL(string: "https://platform.openai.com/api-keys")
        case .anthropic: return URL(string: "https://console.anthropic.com/settings/keys")
        case .gemini:    return URL(string: "https://aistudio.google.com/app/apikey")
        case .kimi:      return URL(string: "https://platform.moonshot.cn/console/api-keys")
        }
    }

    var models: [(id: String, name: String)] {
        switch self {
        case .onDevice:
            return [("system", "Apple Intelligence (default)")]
        case .groq:
            return [
                ("qwen/qwen3-32b",          "Qwen3 32B (best)"),
                ("llama-3.3-70b-versatile", "Llama 3.3 70B"),
                ("llama-3.1-8b-instant",    "Llama 3.1 8B (fastest)"),
            ]
        case .openAI:
            return [
                ("gpt-4o-mini", "GPT-4o Mini (fast)"),
                ("gpt-4o",      "GPT-4o (best)"),
            ]
        case .anthropic:
            return [
                ("claude-3-5-haiku-latest", "Claude 3.5 Haiku (fast)"),
                ("claude-sonnet-4-5",       "Claude Sonnet 4.5 (best)"),
            ]
        case .gemini:
            return [
                ("gemini-2.0-flash",                  "Gemini 2.0 Flash (fast)"),
                ("gemini-2.5-flash-preview-04-17",    "Gemini 2.5 Flash (best)"),
            ]
        case .kimi:
            return [
                ("moonshot-v1-8k",   "Moonshot v1 8K"),
                ("moonshot-v1-32k",  "Moonshot v1 32K"),
                ("moonshot-v1-128k", "Moonshot v1 128K"),
            ]
        }
    }

    var defaultModel: String {
        models.first?.id ?? "default"
    }
}

// MARK: - Settings storage

final class AIProviderSettings {

    static let shared = AIProviderSettings()
    private init() {}

    // MARK: Provider + model (UserDefaults — non-sensitive)

    var selectedProvider: AIProvider {
        get {
            let raw = UserDefaults.standard.string(forKey: "parlance_ai_provider") ?? "groq"
            return AIProvider(rawValue: raw) ?? .groq
        }
        set { UserDefaults.standard.set(newValue.rawValue, forKey: "parlance_ai_provider") }
    }

    func model(for provider: AIProvider) -> String {
        UserDefaults.standard.string(forKey: "parlance_ai_model_\(provider.rawValue)")
            ?? provider.defaultModel
    }

    func setModel(_ model: String, for provider: AIProvider) {
        UserDefaults.standard.set(model, forKey: "parlance_ai_model_\(provider.rawValue)")
    }

    // MARK: API keys (Keychain — sensitive)

    func apiKey(for provider: AIProvider) -> String {
        guard provider.requiresKey else { return "" }
        return KeychainHelper.load(key: keychainKey(provider)) ?? ""
    }

    func setAPIKey(_ key: String, for provider: AIProvider) {
        guard provider.requiresKey else { return }
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
