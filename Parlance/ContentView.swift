import SwiftUI
import WebKit
import Network

struct ContentView: View {
    @State private var showPrivacyPolicy = false
    @State private var showAISettings   = false

    var body: some View {
        ZStack {
            ParlanceWebView()
                .ignoresSafeArea()
                .environment(\.showPrivacyPolicy, $showPrivacyPolicy)
                .environment(\.showAISettings,    $showAISettings)

            if showPrivacyPolicy {
                PrivacyPolicyView(isPresented: $showPrivacyPolicy)
            }
        }
        .sheet(isPresented: $showAISettings) {
            AISettingsView()
        }
    }
}

// MARK: - Environment keys for modal bindings

private struct ShowPrivacyPolicyKey: EnvironmentKey {
    static let defaultValue: Binding<Bool> = .constant(false)
}
private struct ShowAISettingsKey: EnvironmentKey {
    static let defaultValue: Binding<Bool> = .constant(false)
}
extension EnvironmentValues {
    var showPrivacyPolicy: Binding<Bool> {
        get { self[ShowPrivacyPolicyKey.self] }
        set { self[ShowPrivacyPolicyKey.self] = newValue }
    }
    var showAISettings: Binding<Bool> {
        get { self[ShowAISettingsKey.self] }
        set { self[ShowAISettingsKey.self] = newValue }
    }
}

// MARK: - WebView wrapper

struct ParlanceWebView: UIViewRepresentable {
    @Environment(\.showPrivacyPolicy) private var showPrivacyPolicy
    @Environment(\.showAISettings)    private var showAISettings

    func makeCoordinator() -> Coordinator {
        Coordinator(
            showPrivacyPolicy: showPrivacyPolicy,
            showAISettings:    showAISettings
        )
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {
        // Keep coordinator bindings fresh on every SwiftUI update
        context.coordinator.showPrivacyPolicy = showPrivacyPolicy
        context.coordinator.showAISettings    = showAISettings
    }

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.websiteDataStore = WKWebsiteDataStore.default()
        config.allowsInlineMediaPlayback = true

        let contentController = config.userContentController

        // Inject configuration at document start
        let configJSON = buildConfigJSON()
        let injectionScript = "window.__PARLANCE_CONFIG__ = \(configJSON);"
        contentController.addUserScript(WKUserScript(
            source: injectionScript,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true
        ))

        // Listen for messages from JS
        contentController.add(context.coordinator, name: "parlance")

        let webView = WKWebView(frame: .zero, configuration: config)
        webView.scrollView.bounces = false
        webView.isOpaque = false
        webView.backgroundColor = UIColor(red: 0.98, green: 0.97, blue: 0.95, alpha: 1)

        context.coordinator.webView = webView
        context.coordinator.startNetworkMonitor()

        loadHTML(into: webView)
        return webView
    }

    private func buildConfigJSON() -> String {
        // Keep this fast — no Keychain reads, no FoundationModels checks.
        // The native AI provider selection is handled entirely in AISettingsView;
        // the web JS just needs to know it should route through the Swift bridge.
        let groqAvailable = !Config.groqAPIKey.isEmpty
        return """
        {"mode":"unified","onDeviceAvailable":false,"groqAvailable":\(groqAvailable),"activeProvider":"Native"}
        """
    }

    private func loadHTML(into webView: WKWebView) {
        guard let htmlURL = Bundle.main.url(forResource: "index", withExtension: "html") else {
            webView.loadHTMLString(
                "<html><body style='font-family:sans-serif;padding:2rem;color:#555'>" +
                "<h2>Oops</h2><p>index.html not found in app bundle.</p></body></html>",
                baseURL: nil
            )
            return
        }
        let bundleDir = Bundle.main.bundleURL
        webView.loadFileURL(htmlURL, allowingReadAccessTo: bundleDir)
    }

    // MARK: - Coordinator

    class Coordinator: NSObject, WKScriptMessageHandler {
        var showPrivacyPolicy: Binding<Bool>
        var showAISettings:    Binding<Bool>
        weak var webView: WKWebView?
        private let monitor      = NWPathMonitor()
        private let monitorQueue = DispatchQueue(label: "NetworkMonitor")

        init(showPrivacyPolicy: Binding<Bool>, showAISettings: Binding<Bool>) {
            self.showPrivacyPolicy = showPrivacyPolicy
            self.showAISettings    = showAISettings
        }

        func startNetworkMonitor() {
            monitor.pathUpdateHandler = { [weak self] path in
                let isOnline = path.status == .satisfied
                DispatchQueue.main.async {
                    self?.webView?.evaluateJavaScript(
                        "window.dispatchEvent(new CustomEvent('nativeNetworkChange', {detail: {online: \(isOnline)}}))"
                    )
                }
            }
            monitor.start(queue: monitorQueue)
        }

        func userContentController(_ userContentController: WKUserContentController,
                                   didReceive message: WKScriptMessage) {
            if let body = message.body as? String {
                switch body {
                case "showPrivacyPolicy":
                    DispatchQueue.main.async { self.showPrivacyPolicy.wrappedValue = true }
                case "showAISettings":
                    DispatchQueue.main.async { self.showAISettings.wrappedValue = true }
                default:
                    break
                }
                return
            }

            guard let body   = message.body as? [String: Any],
                  let action = body["action"] as? String else { return }

            // analyzeGroq now routes through UnifiedAnalyzer
            if action == "analyzeGroq" || action == "analyzeUnified" {
                handleUnifiedAnalysis(body)
            } else if action == "analyzeOnDevice" {
                handleOnDeviceAnalysis(body)
            }
        }

        private func handleUnifiedAnalysis(_ body: [String: Any]) {
            guard let requestId = body["requestId"] as? String,
                  let sentence  = body["sentence"]  as? String,
                  let language  = body["language"]  as? String,
                  let level     = body["level"]     as? String else { return }

            let ragContext = body["ragContext"] as? String ?? ""

            Task { @MainActor in
                do {
                    let result = try await UnifiedAnalyzer.shared.analyze(
                        sentence: sentence, language: language, level: level, ragContext: ragContext
                    )
                    let jsonData   = try JSONSerialization.data(withJSONObject: result)
                    let jsonString = String(data: jsonData, encoding: .utf8) ?? "{}"
                    try await self.webView?.evaluateJavaScript(
                        "window.__parlanceGroqResult('\(requestId)', \(jsonString), null)"
                    )
                } catch {
                    let escaped = error.localizedDescription
                        .replacingOccurrences(of: "'", with: "\\'")
                        .replacingOccurrences(of: "\n", with: " ")
                    try? await self.webView?.evaluateJavaScript(
                        "window.__parlanceGroqResult('\(requestId)', null, '\(escaped)')"
                    )
                }
            }
        }

        private func handleOnDeviceAnalysis(_ body: [String: Any]) {
            guard let requestId = body["requestId"] as? String,
                  let sentence = body["sentence"] as? String,
                  let language = body["language"] as? String,
                  let level = body["level"] as? String else { return }

            #if canImport(FoundationModels)
            if #available(iOS 26, *) {
                let analyzer = OnDeviceAnalyzer()
                Task { @MainActor in
                    do {
                        let result = try await analyzer.analyze(
                            sentence: sentence, language: language, level: level
                        )
                        let jsonData = try JSONSerialization.data(withJSONObject: result)
                        let jsonString = String(data: jsonData, encoding: .utf8) ?? "{}"
                        try await self.webView?.evaluateJavaScript(
                            "window.__parlanceOnDeviceResult('\(requestId)', \(jsonString), null)"
                        )
                    } catch {
                        let escaped = error.localizedDescription
                            .replacingOccurrences(of: "'", with: "\\'")
                            .replacingOccurrences(of: "\n", with: " ")
                        try? await self.webView?.evaluateJavaScript(
                            "window.__parlanceOnDeviceResult('\(requestId)', null, '\(escaped)')"
                        )
                    }
                }
                return
            }
            #endif

            Task { @MainActor in
                try? await self.webView?.evaluateJavaScript(
                    "window.__parlanceOnDeviceResult('\(requestId)', null, 'On-device analysis not available')"
                )
            }
        }

        deinit {
            monitor.cancel()
        }
    }
}
