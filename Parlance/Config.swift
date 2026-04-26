import Foundation

enum Config {

    private static var configDict: NSDictionary? {
        guard let url = Bundle.main.url(forResource: "Config", withExtension: "plist") else {
            return nil
        }
        return NSDictionary(contentsOf: url)
    }

    static var anthropicAPIKey: String {
        guard
            let dict = configDict,
            let key = dict["ANTHROPIC_API_KEY"] as? String,
            !key.isEmpty,
            key != "YOUR_API_KEY_HERE"
        else {
            print("⚠️ Parlance: No API key found in Config.plist")
            return ""
        }
        return key
    }

    static var proxyURL: String {
        guard
            let dict = configDict,
            let url = dict["PROXY_URL"] as? String,
            !url.isEmpty,
            url != "YOUR_PROXY_URL_HERE"
        else {
            return ""
        }
        return url
    }

    static var useProxy: Bool {
        !proxyURL.isEmpty
    }
}
