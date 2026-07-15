import Foundation

/// Resolves bundled (or cached) MLX weights for Parlance Coach (Spanish / French).
enum ParlanceSLMModelLocator {

    private static let markerFile = "config.json"

    static func folderName(for language: String) -> String? {
        LanguageRegistry.onDeviceModelFolder(for: language)
    }

    /// Directory containing MLX `config.json` and `model.safetensors`, if present.
    static func resolvedModelDirectory(language: String) -> URL? {
        guard let folder = folderName(for: language) else { return nil }
        if let bundled = bundledModelDirectory(folderName: folder) { return bundled }
        return applicationSupportDirectory(folderName: folder)
    }

    static func isModelBundled(language: String) -> Bool {
        guard let folder = folderName(for: language) else { return false }
        return bundledModelDirectory(folderName: folder) != nil
    }

    private static func bundledModelDirectory(folderName: String) -> URL? {
        guard let base = Bundle.main.resourceURL else { return nil }
        let dir = base.appendingPathComponent(folderName, isDirectory: true)
        return directoryIfValid(dir)
    }

    private static func applicationSupportDirectory(folderName: String) -> URL? {
        guard let base = FileManager.default.urls(
            for: .applicationSupportDirectory,
            in: .userDomainMask
        ).first else { return nil }
        let dir = base
            .appendingPathComponent("Parlance", isDirectory: true)
            .appendingPathComponent(folderName, isDirectory: true)
        return directoryIfValid(dir)
    }

    private static func directoryIfValid(_ dir: URL) -> URL? {
        let marker = dir.appendingPathComponent(markerFile)
        var isDir: ObjCBool = false
        guard FileManager.default.fileExists(atPath: marker.path, isDirectory: &isDir),
              !isDir.boolValue else { return nil }
        return dir
    }
}
