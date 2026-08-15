import SwiftUI

/// Native privacy sheet — English content must match `Parlance/web/privacy.html`
/// (canonical source of truth). Mirror: `docs/privacy.html`. Web modal fetches
/// the same HTML. When editing the policy: update privacy.html, copy to docs/,
/// then sync these sections. Swift UI i18n is deferred (issue #25 follow-up).
struct PrivacyPolicyView: View {
    @Binding var isPresented: Bool
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass

    private let intro =
        "Parlance: Interpreter Journal (\"Parlance\", \"we\", \"our\") is built for interpreters and language learners. This policy explains what data we collect, how we use it, and your rights."

    private let sections: [(title: String, body: String)] = [
        (
            "1. On-Device Analysis (Parlance Coach)",
            "When you use Parlance Coach, your sentences are analyzed entirely on your device using a locally stored language model. No sentence text is ever sent to our servers or any third party. This feature works without an internet connection."
        ),
        (
            "2. Cloud AI Analysis",
            "When you choose to use cloud AI analysis, the sentence you submit is sent to Google Firebase Cloud Functions, which routes it to a third-party AI provider (such as Groq, Gemini, OpenAI, or others you select). Sentences are not stored by us after the response is returned. Third-party providers process your input under their own privacy policies."
        ),
        (
            "3. Authentication",
            "Parlance uses Sign in with Apple and Google Sign-In (Firebase Authentication). We use an anonymous User ID (UID) solely to associate your usage quota and call packs with your account. Review Apple's and Google's privacy policies for how they handle sign-in."
        ),
        (
            "4. Usage Counter",
            "We store a single counter in Firestore (Google Cloud) tied to your UID. It tracks how many cloud analysis calls you have made in the current calendar month. It resets monthly and is used only to enforce the 30-call free tier and apply purchased call packs. This counter is never used for advertising, analytics, or any purpose beyond app functionality."
        ),
        (
            "5. In-App Purchases and Parlance Plus",
            "Call pack purchases are processed by Apple. Upon a successful purchase, Apple provides a signed transaction token that we verify server-side. We store a record of the transaction ID and the number of remaining calls in Firestore under your UID. We do not receive or store your payment information.\n\nParlance Plus is an auto-renewing monthly subscription, also processed by Apple. When you subscribe, we verify Apple's signed transaction server-side and store your subscription tier, the original transaction ID, the product ID, the renewal date, and the store environment in Firestore under your UID. We use this only to unlock unlimited cloud AI coaching and the medical and legal interpreting guides. Billing, renewal, and cancellation are handled entirely by Apple in your Apple Account settings, and we never receive your payment information."
        ),
        (
            "6. Journal Entries",
            "Journal entries (titles and sentences) are stored locally on your device. They are not uploaded to our servers."
        ),
        (
            "7. Analytics and Crash Reporting",
            "We do not use third-party analytics SDKs or crash reporting services that collect personal data."
        ),
        (
            "8. Data Retention and Deletion",
            "Your usage and pack records in Firestore are retained as long as your account is active.\n\nYou can delete your account and all of its data from inside the app at any time: open AI settings while signed in, tap Delete account, and confirm. This immediately and permanently removes your Firebase Authentication account, your user profile, your monthly usage counter, your call pack balances, and your Parlance Plus record. It cannot be undone, and remaining call pack balances are not refundable. Journal entries are stored only on your device and are unaffected, so delete them from Past Entries if you also want them gone. If you subscribed to Parlance Plus, cancel the subscription separately in your Apple Account settings so that Apple stops billing it.\n\nIf you cannot access the app, you can also contact us at the address below and we will remove your records within 30 days."
        ),
        (
            "9. Children",
            "Parlance is not directed at children under 13. We do not knowingly collect information from children under 13."
        ),
        (
            "10. Changes to This Policy",
            "We may update this policy. The \"Last updated\" date at the top will reflect any changes. Continued use of the app after changes constitutes acceptance."
        ),
        (
            "11. Contact",
            "Questions? Reach us at github.com/Montrez/ParlanceApp/issues or open an issue on GitHub."
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
                        Text("Last updated: August 14, 2026")
                            .font(.footnote)
                            .foregroundColor(Color("Muted"))

                        Text(intro)
                            .font(.body)
                            .foregroundColor(Color("Ink"))
                            .fixedSize(horizontal: false, vertical: true)

                        ForEach(sections, id: \.title) { section in
                            policySection(title: section.title, body: section.body)
                        }
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
