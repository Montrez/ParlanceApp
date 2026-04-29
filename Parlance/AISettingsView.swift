import SwiftUI

struct AISettingsView: View {

    @Environment(\.dismiss) private var dismiss

    @State private var selectedProvider: AIProvider = AIProviderSettings.shared.selectedProvider
    @State private var selectedModels:   [AIProvider: String] = [:]
    @State private var apiKeys:          [AIProvider: String] = [:]
    @State private var showKeySaved = false

    var body: some View {
        NavigationStack {
            Form {
                providerSection
                if selectedProvider.requiresKey {
                    apiKeySection
                }
                modelSection
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
            if selectedProvider == .onDevice {
                Text("On-device analysis requires Apple Intelligence on iOS 26+.")
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
        #if canImport(FoundationModels)
        return AIProvider.allCases
        #else
        return AIProvider.allCases.filter { $0 != .onDevice }
        #endif
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
}
