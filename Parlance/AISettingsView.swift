import SwiftUI

struct AISettingsView: View {

    @Environment(\.dismiss) private var dismiss
    @Environment(AuthManager.self) private var authManager

    @State private var selectedProvider: AIProvider = AIProviderSettings.shared.selectedProvider
    @State private var selectedModels:   [AIProvider: String] = [:]
    @State private var apiKeys:          [AIProvider: String] = [:]
    @State private var showKeySaved = false
    @State private var authBusy = false

    var body: some View {
        NavigationStack {
            Form {
                authSection
                providerSection
                if selectedProvider.requiresAPIKey(isSignedIn: authManager.isSignedIn) {
                    apiKeySection
                }
                if selectedProvider == .parlanceCoach {
                    parlanceCoachInfoSection
                } else {
                    modelSection
                }
                if selectedProvider == .onDevice {
                    onDeviceInfoSection
                }
                aboutSection
            }
            .navigationTitle("AI Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { saveAndDismiss() }
                        .fontWeight(.semibold)
                }
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
            }
        }
        .onAppear(perform: loadCurrentSettings)
        .overlay(alignment: .bottom) {
            if showKeySaved {
                HStack(spacing: 6) {
                    Image(systemName: "checkmark.circle.fill")
                    Text("Settings saved")
                }
                .font(.system(size: 13, weight: .medium, design: .monospaced))
                .foregroundStyle(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(Color(red: 0.11, green: 0.1, blue: 0.09))
                .clipShape(Capsule())
                .padding(.bottom, 24)
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .animation(.spring(duration: 0.3), value: showKeySaved)
    }

    // MARK: – Auth

    @ViewBuilder
    private var authSection: some View {
        if authManager.isSignedIn {
            Section {
                HStack(alignment: .top, spacing: 10) {
                    Image(systemName: "person.crop.circle.badge.checkmark")
                        .foregroundStyle(.green)
                        .font(.title3)
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Signed in")
                            .font(.subheadline.weight(.semibold))
                        Text(authManager.displayLabel)
                            .font(.subheadline)
                            .foregroundStyle(Color.secondary)
                        Text("Signed-in mode can use cloud AI without API keys (when enabled).")
                            .font(.caption)
                            .foregroundStyle(Color.secondary)
                    }
                }
                .padding(.vertical, 4)

                Button("Sign Out", role: .destructive) {
                    authBusy = true
                    Task {
                        defer { authBusy = false }
                        try? authManager.signOut()
                    }
                }
                .disabled(authBusy)
            } header: {
                Text("Account")
            }
        } else {
            Section {
                Button {
                    authBusy = true
                    Task {
                        defer { authBusy = false }
                        authManager.setPresentationAnchor(ParlanceWebView.activeWebView)
                        do { try await authManager.signInWithApple() }
                        catch AuthManagerError.cancelled { }
                        catch { }
                    }
                } label: {
                    Label("Sign in with Apple", systemImage: "apple.logo")
                }
                .disabled(authBusy)

                if authManager.isGoogleSignInConfigured {
                    Button {
                        authBusy = true
                        Task {
                            defer { authBusy = false }
                            authManager.setPresentationAnchor(ParlanceWebView.activeWebView)
                            do { try await authManager.signInWithGoogle() }
                            catch AuthManagerError.cancelled { }
                            catch { }
                        }
                    } label: {
                        Label("Sign in with Google", systemImage: "globe")
                    }
                    .disabled(authBusy)
                } else {
                    HStack(alignment: .top, spacing: 10) {
                        Image(systemName: "info.circle")
                            .foregroundStyle(Color.secondary)
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Google Sign-In isn’t configured yet.")
                                .font(.subheadline.weight(.semibold))
                            Text("Enable Google in Firebase Authentication, then re-download GoogleService-Info.plist so it includes CLIENT_ID / REVERSED_CLIENT_ID.")
                                .font(.caption)
                                .foregroundStyle(Color.secondary)
                        }
                    }
                    .padding(.vertical, 4)
                }

                if let err = authManager.authError {
                    Text(err)
                        .font(.caption)
                        .foregroundStyle(.red)
                }
            } header: {
                Text("Account")
            } footer: {
                Text("Sign in to use cloud AI without entering API keys (when enabled). Parlance Coach and on-device options work without an account.")
            }
        }
    }

    // MARK: – Sections

    private var providerSection: some View {
        Section {
            ForEach(availableProviders, id: \.rawValue) { provider in
                Button {
                    selectedProvider = provider
                } label: {
                    HStack(spacing: 12) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(provider.displayName)
                                .foregroundStyle(Color.primary)
                                .font(.body)
                            Text(provider.subtitle)
                                .foregroundStyle(Color.secondary)
                                .font(.caption)
                        }
                        Spacer()
                        if selectedProvider == provider {
                            Image(systemName: "checkmark")
                                .foregroundStyle(Color.accentColor)
                                .fontWeight(.semibold)
                        }
                    }
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
            }
        } header: {
            Text("Provider")
        } footer: {
            if selectedProvider == .parlanceCoach {
                Text("Fine-tuned model runs on this device. First analysis may take 1–2 minutes while the model loads.")
            } else if selectedProvider == .onDevice {
                Text("On-device analysis requires Apple Intelligence on iOS 26+.")
            } else if authManager.isSignedIn {
                Text("Your selected cloud provider runs through Parlance when signed in.")
            }
        }
    }

    private var apiKeySection: some View {
        Section {
            SecureField("API key", text: binding(keyFor: selectedProvider))
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .font(.system(.body, design: .monospaced))

            if let url = selectedProvider.keyURL {
                Link(destination: url) {
                    HStack(spacing: 6) {
                        Image(systemName: "key.horizontal")
                        Text("Get a free API key →")
                    }
                    .font(.subheadline)
                    .foregroundStyle(Color.accentColor)
                }
            }
        } header: {
            Text("API Key")
        } footer: {
            Text("Keys are stored securely in the device Keychain and never leave your device except to reach the provider's API.")
        }
    }

    private var modelSection: some View {
        Section("Model") {
            Picker("Model", selection: binding(modelFor: selectedProvider)) {
                ForEach(selectedProvider.models, id: \.id) { m in
                    Text(m.name).tag(m.id)
                }
            }
            .pickerStyle(.menu)
        }
    }

    private var onDeviceInfoSection: some View {
        Section("Privacy") {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: "lock.shield")
                    .foregroundStyle(.green)
                    .font(.title3)
                Text("On-device analysis runs entirely on your iPhone. No data is sent over the internet.")
                    .font(.subheadline)
                    .foregroundStyle(Color.secondary)
            }
            .padding(.vertical, 4)
        }
    }

    private var parlanceCoachInfoSection: some View {
        Section {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: "brain.head.profile")
                    .foregroundStyle(.orange)
                    .font(.title3)
                VStack(alignment: .leading, spacing: 4) {
                    Text("Follows journal language")
                        .font(.subheadline.weight(.semibold))
                    Text(parlanceCoachModelSummary)
                        .font(.subheadline)
                        .foregroundStyle(Color.secondary)
                }
            }
            .padding(.vertical, 4)
        } header: {
            Text("Model")
        } footer: {
            Text("Spanish and French models switch automatically based on the language you write in.")
        }
    }

    private var parlanceCoachModelSummary: String {
        let langs = ParlanceSLMAnalyzer.availableCoachLanguages()
        if langs.isEmpty {
            return "Not bundled in this build. Run ./training/prepare_ios_coach_model.sh and re-archive."
        }
        return langs.map { $0 == "fr" ? "French" : "Spanish" }.joined(separator: " · ")
    }

    private var aboutSection: some View {
        Section {
            HStack {
                Text("Current provider")
                Spacer()
                Text(selectedProvider.displayName)
                    .foregroundStyle(Color.secondary)
                    .font(.subheadline)
            }
        } header: {
            Text("About")
        } footer: {
            Text("Parlance uses your sentences to provide grammar feedback. Your journal entries are stored only on your device.")
        }
    }

    // MARK: – Helpers

    private var availableProviders: [AIProvider] {
        var list = AIProvider.allCases.filter { provider in
            if provider == .onDevice {
                #if canImport(FoundationModels)
                return true
                #else
                return false
                #endif
            }
            if provider == .parlanceCoach {
                return ParlanceSLMAnalyzer.isOnDeviceModelAvailable
            }
            return true
        }

        if let coachIndex = list.firstIndex(of: .parlanceCoach), coachIndex > 0 {
            list.remove(at: coachIndex)
            list.insert(.parlanceCoach, at: 0)
        }
        return list
    }

    private func loadCurrentSettings() {
        selectedProvider = AIProviderSettings.shared.selectedProvider
        for p in AIProvider.allCases {
            selectedModels[p] = AIProviderSettings.shared.model(for: p)
            apiKeys[p]        = AIProviderSettings.shared.apiKey(for: p)
        }
    }

    private func saveAndDismiss() {
        AIProviderSettings.shared.selectedProvider = selectedProvider
        for p in AIProvider.allCases {
            if let m = selectedModels[p] { AIProviderSettings.shared.setModel(m, for: p) }
            if let k = apiKeys[p]        { AIProviderSettings.shared.setAPIKey(k, for: p) }
        }
        if selectedProvider == .parlanceCoach {
            let lang = UserDefaults.standard.string(forKey: "parlance_language") ?? "es"
            let modelId = lang == "fr" ? "parlance-fr" : "parlance-es"
            AIProviderSettings.shared.setModel(modelId, for: .parlanceCoach)
        }

        withAnimation { showKeySaved = true }
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.4) {
            withAnimation { showKeySaved = false }
            dismiss()
        }
    }

    private func binding(keyFor provider: AIProvider) -> Binding<String> {
        Binding(
            get: { apiKeys[provider] ?? "" },
            set: { apiKeys[provider] = $0 }
        )
    }

    private func binding(modelFor provider: AIProvider) -> Binding<String> {
        Binding(
            get: { selectedModels[provider] ?? provider.defaultModel },
            set: { selectedModels[provider] = $0 }
        )
    }
}

#Preview {
    AISettingsView()
        .environment(AuthManager.shared)
}
