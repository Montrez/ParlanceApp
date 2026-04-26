import SwiftUI

struct PrivacyPolicyView: View {
    @Binding var isPresented: Bool

    var body: some View {
        ZStack {
            Color.black.opacity(0.4)
                .ignoresSafeArea()
                .onTapGesture { isPresented = false }

            VStack(spacing: 0) {
                HStack {
                    Text("Privacy Policy")
                        .font(.custom("Georgia", size: 20))
                        .fontWeight(.bold)
                    Spacer()
                    Button { isPresented = false } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.title2)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding()

                Divider()

                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        policySection(
                            title: "What Parlance Does",
                            body: "Parlance is a language writing coach that helps you practice writing in multiple languages. You write sentences and receive real-time feedback on grammar, naturalness, and word choice."
                        )

                        policySection(
                            title: "Data Stored on Your Device",
                            body: "Your journal entries are saved locally on your device using your browser's storage. They never leave your device unless you choose to share them. No account or sign-up is required."
                        )

                        policySection(
                            title: "Data Sent for Analysis",
                            body: "When you write a sentence, it is sent to the Anthropic API (api.anthropic.com) to generate feedback. Only the sentence text and your selected proficiency level are transmitted. Anthropic's usage policy governs how they handle this data. No personal information is included in these requests."
                        )

                        policySection(
                            title: "No Tracking or Analytics",
                            body: "Parlance does not use any analytics services, advertising SDKs, or tracking pixels. We do not collect usage statistics, device identifiers, or location data."
                        )

                        policySection(
                            title: "No Data Sold",
                            body: "We do not sell, rent, or share any of your data with third parties."
                        )

                        policySection(
                            title: "Third-Party Services",
                            body: "Parlance uses Google Fonts (fonts.googleapis.com, fonts.gstatic.com) to load display typefaces. Google's privacy policy applies to font loading. The Anthropic API is used for sentence analysis. No other third-party services are used."
                        )

                        policySection(
                            title: "Contact",
                            body: "If you have questions about this privacy policy, contact mojcox@gmail.com."
                        )

                        Text("Last updated: April 2026")
                            .font(.custom("Georgia", size: 12))
                            .foregroundColor(Color(red: 0.45, green: 0.42, blue: 0.38))
                            .padding(.top, 8)
                    }
                    .padding()
                }
            }
            .background(Color(red: 0.98, green: 0.97, blue: 0.95))
            .clipShape(RoundedRectangle(cornerRadius: 16))
            .shadow(radius: 20)
            .padding(24)
        }
        .transition(.opacity)
        .animation(.easeInOut(duration: 0.2), value: isPresented)
    }

    private func policySection(title: String, body: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.custom("Georgia", size: 15))
                .fontWeight(.bold)
                .foregroundColor(Color(red: 0.11, green: 0.09, blue: 0.08))
            Text(body)
                .font(.custom("Georgia", size: 14))
                .foregroundColor(Color(red: 0.25, green: 0.22, blue: 0.20))
                .lineSpacing(4)
        }
    }
}
