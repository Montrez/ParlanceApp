import SwiftUI

/// Native privacy sheet — content aligned with `docs/privacy.html` (App Store / public policy).
/// Full i18n consolidation across web modal + docs remains tracked in issue #25.
struct PrivacyPolicyView: View {
    @Binding var isPresented: Bool
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass

    private let sections: [(title: String, body: String)] = [
        (
            "On-Device Analysis (Parlance Coach)",
            "When you use Parlance Coach, your sentences are analyzed entirely on your device using a locally stored language model. No sentence text is ever sent to our servers or any third party. This feature works without an internet connection."
        ),
        (
            "Cloud AI Analysis",
            "When you choose to use cloud AI analysis, the sentence you submit is sent to Google Firebase Cloud Functions, which routes it to a third-party AI provider (such as Groq, Gemini, OpenAI, or others you select). Sentences are not stored by us after the response is returned. Third-party providers process your input under their own privacy policies."
        ),
        (
            "Authentication",
            "Parlance uses Sign in with Apple and Google Sign-In (Firebase Authentication). We use an anonymous User ID (UID) solely to associate your usage quota and call packs with your account. Review Apple’s and Google’s privacy policies for how they handle sign-in."
        ),
        (
            "Usage Counter",
            "We store a single counter in Firestore (Google Cloud) tied to your UID. It tracks how many cloud analysis calls you have made in the current calendar month. It resets monthly and is used only to enforce the free tier and apply purchased call packs. This counter is never used for advertising or analytics."
        ),
        (
            "In-App Purchases",
            "Call pack purchases are processed by Apple. Upon a successful purchase, Apple provides a signed transaction token that we verify server-side. We store a record of the transaction ID and remaining calls in Firestore under your UID. We do not receive or store your payment information."
        ),
        (
            "Journal Entries",
            "Journal entries (titles and sentences) are stored locally on your device. They are not uploaded to our servers."
        ),
        (
            "Analytics and Crash Reporting",
            "We do not use third-party analytics SDKs or crash reporting services that collect personal data."
        ),
        (
            "Data Retention and Deletion",
            "Your usage and pack records in Firestore are retained as long as your account is active. To request deletion of your data, contact us and we will remove your records within 30 days."
        ),
        (
            "Children",
            "Parlance is not directed at children under 13. We do not knowingly collect information from children under 13."
        ),
        (
            "Contact",
            "Questions? Open an issue at github.com/Montrez/ParlanceApp/issues."
        ),
    ]

    var body: some View {
        ZStack {
            Color.black.opacity(0.4)
                .ignoresSafeArea()
                .onTapGesture { isPresented = false }

            VStack(spacing: 0) {
                HStack {
                    Text("Privacy Policy")
                        .font(.title2.weight(.semibold))
                    Spacer()
                    Button { isPresented = false } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.title2)
                            .foregroundStyle(.secondary)
                    }
                    .accessibilityLabel("Close")
                }
                .padding()

                Divider()

                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        ForEach(sections, id: \.title) { section in
                            policySection(title: section.title, body: section.body)
                        }

                        Text("Last updated: July 2026")
                            .font(.footnote)
                            .foregroundColor(Color("Muted"))
                            .padding(.top, 8)
                    }
                    .padding()
                }
            }
            .background(Color("Paper"))
            .clipShape(RoundedRectangle(cornerRadius: 16))
            .shadow(radius: 20)
            .frame(maxWidth: horizontalSizeClass == .regular ? 640 : 520)
            .padding(horizontalSizeClass == .regular ? 40 : 24)
        }
        .transition(.opacity)
    }

    private func policySection(title: String, body: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.headline)
                .foregroundColor(Color("Ink"))
            Text(body)
                .font(.body)
                .foregroundColor(Color("Ink"))
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}
