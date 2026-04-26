import Foundation

enum Config {

    private static var secretsDict: NSDictionary? {
        guard let url = Bundle.main.url(forResource: "Secrets", withExtension: "plist") else {
            return nil
        }
        return NSDictionary(contentsOf: url)
    }

    private static var configDict: NSDictionary? {
        guard let url = Bundle.main.url(forResource: "Config", withExtension: "plist") else {
            return nil
        }
        return NSDictionary(contentsOf: url)
    }

    private static func value(forKey key: String) -> String? {
        if let val = secretsDict?[key] as? String, !val.isEmpty {
            return val
        }
        if let val = ProcessInfo.processInfo.environment[key], !val.isEmpty {
            return val
        }
        if let val = configDict?[key] as? String, !val.isEmpty, !val.hasPrefix("YOUR_") {
            return val
        }
        return nil
    }

    static var anthropicAPIKey: String {
        guard let key = value(forKey: "ANTHROPIC_API_KEY") else {
            print("⚠️ Parlance: No API key found. Add it to Secrets.plist or set ANTHROPIC_API_KEY env var.")
            return ""
        }
        return key
    }

    static var proxyURL: String {
        value(forKey: "PROXY_URL") ?? ""
    }

    static var useProxy: Bool {
        !proxyURL.isEmpty
    }
}
