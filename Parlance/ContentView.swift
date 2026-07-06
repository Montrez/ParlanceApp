import SwiftUI
import WebKit
import Network

struct ContentView: View {
    @Environment(AuthManager.self) private var authManager
    @State private var showPrivacyPolicy = false
    @State private var showAISettings   = false
    @State private var aiSettingsRefreshId = UUID()

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
        .sheet(isPresented: $showAISettings, onDismiss: {
            syncAISettingsToWeb()
        }) {
            AISettingsView()
                .id(aiSettingsRefreshId)
                .environment(authManager)
        }
        .onChange(of: showAISettings) { _, showing in
            if showing {
                syncAISettingsFromWeb {
                    aiSettingsRefreshId = UUID()
                }
            }
        }
        .onChange(of: authManager.isSignedIn) { _, _ in
            authManager.injectAuth(into: ParlanceWebView.activeWebView)
        }
        .onChange(of: authManager.displayLabel) { _, _ in
            authManager.injectAuth(into: ParlanceWebView.activeWebView)
        }
    }

    private func syncAISettingsFromWeb(completion: (() -> Void)? = nil) {
        guard let webView = ParlanceWebView.activeWebView else {
            completion?()
            return
        }
        webView.evaluateJavaScript(
            """
            (function(){
              var p=localStorage.getItem('parlance_ai_provider')||'parlance';
              var m=localStorage.getItem('parlance_ai_model_'+p)||'';
              var lang=localStorage.getItem('parlance_language')||'es';
              return JSON.stringify({provider:p,model:m,language:lang});
            })()
            """
        ) { result, _ in
            if let json = result as? String,
               let data = json.data(using: .utf8),
               let obj = try? JSONSerialization.jsonObject(with: data) as? [String: String],
               let providerId = obj["provider"] {
                if let lang = obj["language"] {
                    UserDefaults.standard.set(lang, forKey: "parlance_language")
                }

                let provider = Self.nativeProvider(fromWebId: providerId)
                AIProviderSettings.shared.selectedProvider = provider

                if provider == .parlanceCoach {
                    let lang = obj["language"] ?? UserDefaults.standard.string(forKey: "parlance_language") ?? "es"
                    let modelId = lang == "fr" ? "parlance-fr" : "parlance-es"
                    AIProviderSettings.shared.setModel(modelId, for: .parlanceCoach)
                } else if let model = obj["model"], !model.isEmpty {
                    AIProviderSettings.shared.setModel(model, for: provider)
                }
            }
            DispatchQueue.main.async { completion?() }
        }
    }

    private func syncAISettingsToWeb() {
        guard let webView = ParlanceWebView.activeWebView else { return }
        let provider = AIProviderSettings.shared.selectedProvider

        if provider == .parlanceCoach {
            webView.evaluateJavaScript(
                """
                (function(){
                  var lang=localStorage.getItem('parlance_language')||'es';
                  return lang==='fr'?'parlance-fr':'parlance-es';
                })()
                """
            ) { result, _ in
                let model = (result as? String) ?? "parlance-es"
                webView.evaluateJavaScript(
                    "if(typeof applyNativeAISettings==='function')applyNativeAISettings('parlance','\(Self.jsSingleQuoted(model))');"
                ) { _, _ in }
            }
            return
        }

        guard provider != .onDevice else { return }
        let webId = Self.webProviderId(for: provider)
        let model = AIProviderSettings.shared.model(for: provider)
        webView.evaluateJavaScript(
            "if(typeof applyNativeAISettings==='function')applyNativeAISettings('\(webId)','\(Self.jsSingleQuoted(model))');"
        ) { _, _ in }
    }

    private static func nativeProvider(fromWebId id: String) -> AIProvider {
        if id == "parlance" { return .parlanceCoach }
        if let mapped = FirebaseCloudAnalyzer.provider(fromWebId: id) { return mapped }
        if let provider = AIProvider(rawValue: id) { return provider }
        return ParlanceSLMAnalyzer.isOnDeviceModelAvailable ? .parlanceCoach : .groq
    }

    private static func webProviderId(for provider: AIProvider) -> String {
        provider.webProviderId
    }

    private static func jsSingleQuoted(_ str: String) -> String {
        str.replacingOccurrences(of: "\\", with: "\\\\")
           .replacingOccurrences(of: "'", with: "\\'")
           .replacingOccurrences(of: "\n", with: "\\n")
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
    @Environment(AuthManager.self) private var authManager

    /// Latest WKWebView for auth injection from SwiftUI `onChange`.
    static weak var activeWebView: WKWebView?

    func makeCoordinator() -> Coordinator {
        Coordinator(
            showPrivacyPolicy: showPrivacyPolicy,
            showAISettings:    showAISettings,
            authManager:       authManager
        )
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {
        context.coordinator.showPrivacyPolicy = showPrivacyPolicy
        context.coordinator.showAISettings    = showAISettings
        context.coordinator.authManager       = authManager
        Self.activeWebView = uiView
        authManager.injectAuth(into: uiView)
    }

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.websiteDataStore = WKWebsiteDataStore.default()
        config.allowsInlineMediaPlayback = true

        let contentController = config.userContentController

        // Inject configuration at document start
        let configJSON = buildConfigJSON()
        let injectionScript = """
        window.__PARLANCE_CONFIG__ = \(configJSON);
        window.__PARLANCE_AUTH__ = \(context.coordinator.authManager.authInjectionJSON());
        """
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
        Self.activeWebView = webView
        context.coordinator.startNetworkMonitor()

        loadHTML(into: webView)
        DispatchQueue.main.async {
            authManager.injectAuth(into: webView)
        }
        return webView
    }

    private func buildConfigJSON() -> String {
        let providerName = UnifiedAnalyzer.shared.activeProviderName
        var onDeviceAvail = false
        #if canImport(FoundationModels)
        if #available(iOS 26, *) {
            onDeviceAvail = OnDeviceAnalyzer.isAvailable
        }
        #endif
        let coachLangs = ParlanceSLMAnalyzer.availableCoachLanguages()
        let coachAvailable = !coachLangs.isEmpty
        let langsJSON = coachLangs.map { "\"\($0)\"" }.joined(separator: ",")
        return """
        {"mode":"unified","onDeviceAvailable":\(onDeviceAvail),"groqAvailable":true,"activeProvider":"\(providerName)","parlanceCoachAvailable":\(coachAvailable),"parlanceCoachLanguages":[\(langsJSON)]}
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
        var authManager: AuthManager
        weak var webView: WKWebView?
        private let monitor      = NWPathMonitor()
        private let monitorQueue = DispatchQueue(label: "NetworkMonitor")

        init(showPrivacyPolicy: Binding<Bool>, showAISettings: Binding<Bool>, authManager: AuthManager) {
            self.showPrivacyPolicy = showPrivacyPolicy
            self.showAISettings    = showAISettings
            self.authManager       = authManager
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

            if action == "analyzeFirebase" {
                handleFirebaseAnalysis(body)
            } else if action == "analyzeGroq" || action == "analyzeUnified" {
                handleUnifiedAnalysis(body)
            } else if action == "analyzeParlanceSLM" {
                handleParlanceSLMAnalysis(body)
            } else if action == "unloadParlanceSLM" {
                Task {
                    await ParlanceSLMEngine.shared.unload()
                }
            } else if action == "analyzeOnDevice" {
                handleOnDeviceAnalysis(body)
            } else if action == "signInApple" {
                handleSignInApple(body)
            } else if action == "signInGoogle" {
                handleSignInGoogle(body)
            } else if action == "signOut" {
                handleSignOut(body)
            } else if action == "purchaseCallPack" {
                handlePurchaseCallPack(body)
            }
        }

        private func handleUnifiedAnalysis(_ body: [String: Any]) {
            guard let requestId = body["requestId"] as? String,
                  let sentence  = body["sentence"]  as? String,
                  let language  = body["language"]  as? String else { return }

            let level = body["level"] as? String ?? ""
            let ragContext = body["ragContext"] as? String ?? ""

            Task { @MainActor in
                do {
                    let result = try await UnifiedAnalyzer.shared.analyze(
                        sentence: sentence,
                        language: language,
                        level: level,
                        ragContext: ragContext,
                        isSignedIn: authManager.isSignedIn
                    )
                    let jsonData   = try JSONSerialization.data(withJSONObject: result)
                    let jsonString = String(data: jsonData, encoding: .utf8) ?? "{}"
                    self.webView?.evaluateJavaScript(
                        "window.__parlanceGroqResult('\(requestId)', \(jsonString), null)"
                    ) { _, jsErr in
                        if let jsErr { print("[Parlance] JS callback error:", jsErr) }
                    }
                } catch {
                    print("[Parlance] Analysis failed:", error.localizedDescription)
                    let errJSON = Self.jsonEscaped(error.localizedDescription)
                    self.webView?.evaluateJavaScript(
                        "window.__parlanceGroqResult(\"\(requestId)\", null, \"\(errJSON)\")"
                    ) { _, jsErr in
                        if let jsErr { print("[Parlance] JS error callback failed:", jsErr) }
                    }
                }
            }
        }

        private func handleFirebaseAnalysis(_ body: [String: Any]) {
            guard let requestId = body["requestId"] as? String,
                  let sentence  = body["sentence"]  as? String,
                  let language  = body["language"]  as? String else { return }

            let level = body["level"] as? String ?? ""
            let ragContext   = body["ragContext"] as? String ?? ""
            let providerId   = (body["provider"] as? String) ?? (body["providerId"] as? String)
            let model        = body["model"] as? String

            Task { @MainActor in
                guard authManager.isSignedIn else {
                    let errJSON = Self.jsonEscaped("Sign in required for cloud analysis.")
                    self.webView?.evaluateJavaScript(
                        "window.__parlanceFirebaseResult(\"\(requestId)\", null, \"\(errJSON)\")"
                    ) { _, _ in }
                    return
                }

                do {
                    let result = try await UnifiedAnalyzer.shared.analyze(
                        sentence: sentence,
                        language: language,
                        level: level,
                        ragContext: ragContext,
                        isSignedIn: true,
                        webProviderId: providerId,
                        webModel: model
                    )
                    let jsonData   = try JSONSerialization.data(withJSONObject: result)
                    let jsonString = String(data: jsonData, encoding: .utf8) ?? "{}"
                    self.webView?.evaluateJavaScript(
                        "window.__parlanceFirebaseResult('\(requestId)', \(jsonString), null)"
                    ) { _, jsErr in
                        if let jsErr { print("[Parlance] Firebase JS callback error:", jsErr) }
                    }
                } catch {
                    print("[Parlance] Firebase analysis failed:", error.localizedDescription)
                    let errJSON = Self.jsonEscaped(error.localizedDescription)
                    self.webView?.evaluateJavaScript(
                        "window.__parlanceFirebaseResult(\"\(requestId)\", null, \"\(errJSON)\")"
                    ) { _, _ in }
                }
            }
        }

        private static func jsonEscaped(_ str: String) -> String {
            str.replacingOccurrences(of: "\\", with: "\\\\")
               .replacingOccurrences(of: "\"", with: "\\\"")
               .replacingOccurrences(of: "\n", with: "\\n")
               .replacingOccurrences(of: "\r", with: "\\r")
               .replacingOccurrences(of: "\t", with: "\\t")
        }

        private func completeAuthRequest(_ requestId: String, error: String?) {
            let errJS: String
            if let error {
                errJS = "\"\(Self.jsonEscaped(error))\""
            } else {
                errJS = "null"
            }
            webView?.evaluateJavaScript(
                "window.__parlanceAuthResult(\"\(requestId)\", \(errJS))"
            ) { _, _ in }
        }

        private func handleSignInApple(_ body: [String: Any]) {
            guard let requestId = body["requestId"] as? String else { return }
            Task { @MainActor in
                do {
                    try await authManager.signInWithApple()
                    authManager.injectAuth(into: webView)
                    completeAuthRequest(requestId, error: nil)
                } catch AuthManagerError.cancelled {
                    completeAuthRequest(requestId, error: "cancelled")
                } catch {
                    completeAuthRequest(requestId, error: error.localizedDescription)
                }
            }
        }

        private func handleSignInGoogle(_ body: [String: Any]) {
            guard let requestId = body["requestId"] as? String else { return }
            Task { @MainActor in
                do {
                    try await authManager.signInWithGoogle()
                    authManager.injectAuth(into: webView)
                    completeAuthRequest(requestId, error: nil)
                } catch AuthManagerError.cancelled {
                    completeAuthRequest(requestId, error: "cancelled")
                } catch {
                    completeAuthRequest(requestId, error: error.localizedDescription)
                }
            }
        }

        private func handleSignOut(_ body: [String: Any]) {
            guard let requestId = body["requestId"] as? String else { return }
            Task { @MainActor in
                do {
                    try authManager.signOut()
                    authManager.injectAuth(into: webView)
                    completeAuthRequest(requestId, error: nil)
                } catch {
                    completeAuthRequest(requestId, error: error.localizedDescription)
                }
            }
        }

        private func handleParlanceSLMAnalysis(_ body: [String: Any]) {
            guard let requestId = body["requestId"] as? String,
                  let sentence  = body["sentence"]  as? String,
                  let language  = body["language"]  as? String else { return }

            let level = body["level"] as? String ?? ""
            let ragContext = body["ragContext"] as? String ?? ""

            Task { @MainActor in
                do {
                    guard await ParlanceSLMAnalyzer.isAvailable(language: language) else {
                        throw ParlanceSLMError.modelMissing
                    }

                    let result = try await ParlanceSLMAnalyzer.analyze(
                        sentence: sentence, language: language, level: level, ragContext: ragContext
                    )
                    let jsonData   = try JSONSerialization.data(withJSONObject: result)
                    let jsonString = String(data: jsonData, encoding: .utf8) ?? "{}"
                    self.webView?.evaluateJavaScript(
                        "window.__parlanceSLMResult('\(requestId)', \(jsonString), null)"
                    ) { _, jsErr in
                        if let jsErr { print("[Parlance] SLM JS callback error:", jsErr) }
                    }
                } catch {
                    let errJSON = Self.jsonEscaped(error.localizedDescription)
                    self.webView?.evaluateJavaScript(
                        "window.__parlanceSLMResult(\"\(requestId)\", null, \"\(errJSON)\")"
                    ) { _, _ in }
                }
            }
        }

        private func handleOnDeviceAnalysis(_ body: [String: Any]) {
            guard let requestId = body["requestId"] as? String,
                  let sentence = body["sentence"] as? String,
                  let language = body["language"] as? String else { return }

            let level = body["level"] as? String ?? ""

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
                        self.webView?.evaluateJavaScript(
                            "window.__parlanceOnDeviceResult('\(requestId)', \(jsonString), null)"
                        ) { _, jsErr in
                            if let jsErr { print("[Parlance] JS on-device callback error:", jsErr) }
                        }
                    } catch {
                        print("[Parlance] On-device analysis failed:", error.localizedDescription)
                        let errJSON = Self.jsonEscaped(error.localizedDescription)
                        self.webView?.evaluateJavaScript(
                            "window.__parlanceOnDeviceResult(\"\(requestId)\", null, \"\(errJSON)\")"
                        ) { _, _ in }
                    }
                }
                return
            }
            #endif

            self.webView?.evaluateJavaScript(
                "window.__parlanceOnDeviceResult(\"\(requestId)\", null, \"On-device analysis not available\")"
            ) { _, _ in }
        }

        private func handlePurchaseCallPack(_ body: [String: Any]) {
            guard let requestId = body["requestId"] as? String else { return }
            Task { @MainActor in
                let result = await StoreKitManager.shared.purchaseCallPack()
                switch result {
                case .success(let transactionId):
                    let escaped = Self.jsonEscaped(transactionId)
                    self.webView?.evaluateJavaScript(
                        "window.__parlancePurchaseResult(\"\(requestId)\", {success:true,transactionId:\"\(escaped)\"}, null)"
                    ) { _, _ in }
                case .cancelled:
                    self.webView?.evaluateJavaScript(
                        "window.__parlancePurchaseResult(\"\(requestId)\", null, \"cancelled\")"
                    ) { _, _ in }
                case .failed(let msg):
                    let escaped = Self.jsonEscaped(msg)
                    self.webView?.evaluateJavaScript(
                        "window.__parlancePurchaseResult(\"\(requestId)\", null, \"\(escaped)\")"
                    ) { _, _ in }
                }
            }
        }

        deinit {
            monitor.cancel()
        }
    }
}
