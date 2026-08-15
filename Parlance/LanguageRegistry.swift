import Foundation

/// Single source of truth for which languages Parlance supports for journaling and
/// Parlance Coach, and their metadata (display name, on-device model bundle folder).
///
/// To add a language: add a row here, add its content (guides, prompts, RAG knowledge)
/// and — if it should have an on-device Coach model — its bundled MLX weights folder.
/// Do not add new `language == "xx"` branches in analyzer/UI code; look it up here instead.
struct LanguageInfo {
    let code: String
    /// English display name used in AI prompts and native UI (e.g. "Spanish").
    let displayName: String
    /// Bundled MLX weights folder name under `Parlance/Models/`. `nil` if there is no
    /// on-device Parlance Coach model for this language (cloud providers can still work).
    let onDeviceModelFolder: String?
}

enum LanguageRegistry {
    static let all: [LanguageInfo] = [
        LanguageInfo(code: "es", displayName: "Spanish", onDeviceModelFolder: "parlance-es-mlx"),
        LanguageInfo(code: "fr", displayName: "French", onDeviceModelFolder: "parlance-fr-mlx"),
        // English uses the same multilingual Qwen 0.5B (Spanish export) until
        // dedicated English weights ship. Prompts and sanitize are English-specific.
        LanguageInfo(code: "en", displayName: "English", onDeviceModelFolder: "parlance-es-mlx"),
    ]

    private static let byCode: [String: LanguageInfo] = Dictionary(
        uniqueKeysWithValues: all.map { ($0.code, $0) }
    )

    static func info(for code: String) -> LanguageInfo? {
        byCode[code]
    }

    static func isKnown(_ code: String) -> Bool {
        byCode[code] != nil
    }

    /// English display name for prompts/UI. Falls back to the raw code (uppercased) for
    /// an unrecognized language rather than silently guessing "Spanish" or "French".
    static func displayName(for code: String) -> String {
        byCode[code]?.displayName ?? code.uppercased()
    }

    /// Language codes that have a bundled (or downloadable) on-device Coach model.
    static var onDeviceSupportedCodes: [String] {
        all.compactMap { $0.onDeviceModelFolder != nil ? $0.code : nil }
    }

    static func onDeviceModelFolder(for code: String) -> String? {
        byCode[code]?.onDeviceModelFolder
    }

    /// GGUF / JS storage id (`parlance-es`, `parlance-fr`). English shares the
    /// Spanish 0.5B file until a dedicated English export exists.
    static func slmStorageId(for code: String) -> String {
        code == "fr" ? "parlance-fr" : "parlance-es"
    }
}
