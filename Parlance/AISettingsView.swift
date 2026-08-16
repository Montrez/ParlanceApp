import SwiftUI

struct AISettingsView: View {

    @Environment(\.dismiss) private var dismiss

    @State private var showKeySaved = false
    @ObservedObject private var storeKit = StoreKitManager.shared
    @State private var plusBusy = false
    @State private var plusDetailsOpen = false

    var body: some View {
        NavigationStack {
            Form {
                plusSection
                parlanceCoachInfoSection
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
                .foregroundStyle(Color("Paper"))
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(Color("Ink"))
                .clipShape(Capsule())
                .padding(.bottom, 24)
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .animation(.spring(duration: 0.3), value: showKeySaved)
    }

    // MARK: – Parlance Plus

    private var plusBenefits: [String] {
        [
            "Unlimited Coach feedback — no analysis cap",
            "Medical interpreting guide — clinical vocabulary, register, and ethics",
            "Legal interpreting guide — court roles, rights language, and protocol",
            "Coach adds medical or legal context when a journal sentence uses those terms",
        ]
    }

    private var plusSection: some View {
        Section {
            Text(storeKit.isPlusActive
                 ? "You have Parlance Plus. Here is what that includes."
                 : "Parlance Plus unlocks unlimited feedback and the domain guides.")
                .font(.subheadline)
                .foregroundStyle(Color.secondary)

            if storeKit.isPlusActive {
                plusBenefitList
            } else {
                DisclosureGroup(isExpanded: $plusDetailsOpen) {
                    plusBenefitList
                } label: {
                    Text("See what's included")
                        .font(.subheadline)
                }
            }

            if !storeKit.isPlusActive {
                Button("Subscribe to Parlance Plus") {
                    plusBusy = true
                    Task {
                        defer { plusBusy = false }
                        _ = await storeKit.purchasePlus()
                    }
                }
                .disabled(plusBusy || !storeKit.isPlusPurchasable)

                Button("Restore purchase") {
                    plusBusy = true
                    Task {
                        defer { plusBusy = false }
                        _ = await storeKit.restorePlus()
                    }
                }
                .disabled(plusBusy)
            }
        } header: {
            Text("Your Parlance Plus")
        }
    }

    private var plusBenefitList: some View {
        ForEach(plusBenefits, id: \.self) { benefit in
            HStack(alignment: .top, spacing: 10) {
                Text(storeKit.isPlusActive ? "Included" : "Locked")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(storeKit.isPlusActive ? Color.green : Color.secondary)
                    .frame(width: 64, alignment: .leading)
                Text(benefit)
                    .font(.subheadline)
            }
        }
    }

    // MARK: – Sections

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
            Text("Parlance Coach runs on this iPhone. English, Spanish, and French switch with the language you write in. First analysis may take a minute while the model loads.")
        }
    }

    private var parlanceCoachModelSummary: String {
        let langs = ParlanceSLMAnalyzer.availableCoachLanguages()
        if langs.isEmpty {
            return "Coach is still installing on this iPhone. Keep the app open, then try again."
        }
        return langs.map { LanguageRegistry.displayName(for: $0) }.joined(separator: " · ")
    }

    private var aboutSection: some View {
        Section {
            HStack {
                Text("Current provider")
                Spacer()
                Text("Parlance Coach")
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

    private func loadCurrentSettings() {
        AIProviderSettings.shared.selectedProvider = .parlanceCoach
        let lang = UserDefaults.standard.string(forKey: "parlance_language") ?? "es"
        let modelId = LanguageRegistry.slmStorageId(for: lang)
        AIProviderSettings.shared.setModel(modelId, for: .parlanceCoach)
    }

    private func saveAndDismiss() {
        AIProviderSettings.shared.selectedProvider = .parlanceCoach
        let lang = UserDefaults.standard.string(forKey: "parlance_language") ?? "es"
        let modelId = LanguageRegistry.slmStorageId(for: lang)
        AIProviderSettings.shared.setModel(modelId, for: .parlanceCoach)

        withAnimation { showKeySaved = true }
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.4) {
            withAnimation { showKeySaved = false }
            dismiss()
        }
    }
}

#Preview {
    AISettingsView()
        .environment(AuthManager.shared)
}
