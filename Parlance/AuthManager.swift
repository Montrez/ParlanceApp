import AuthenticationServices
import CryptoKit
import FirebaseAuth
import FirebaseCore
import FirebaseFunctions
import GoogleSignIn
import Observation
import UIKit
import WebKit

enum AuthManagerError: LocalizedError {
    case cancelled
    case missingGoogleClientID
    case noPresenter
    case missingIDToken
    case notSignedIn
    case serverDataDeleteFailed

    var errorDescription: String? {
        switch self {
        case .cancelled:
            return nil
        case .missingGoogleClientID:
            return "Google Sign-In is not configured. Enable Google in Firebase Authentication and re-download GoogleService-Info.plist."
        case .noPresenter:
            return "Could not present sign-in UI."
        case .missingIDToken:
            return "Sign-in did not return an ID token."
        case .notSignedIn:
            return "You are not signed in."
        case .serverDataDeleteFailed:
            return "Could not delete your Parlance data. Check your connection and try again."
        }
    }
}

@Observable
@MainActor
final class AuthManager: NSObject {

    static let shared = AuthManager()

    private(set) var user: User?
    private(set) var isSignedIn = false
    private(set) var authError: String?

    /// Apple's `ASAuthorizationController` is used both to sign in and to prove
    /// recent login before deletion, and Firebase needs a different call in each
    /// case, so the delegate has to know which one is in flight.
    private enum AppleFlow {
        case signIn
        case reauthenticate
    }

    private var authListener: AuthStateDidChangeListenerHandle?
    private var currentNonce: String?
    private var appleSignInContinuation: CheckedContinuation<Void, Error>?
    private var appleSignInController: ASAuthorizationController?
    private var appleFlow: AppleFlow = .signIn
    /// Apple only hands out an authorization code during an authorization, and
    /// revoking the Sign in with Apple token at deletion time requires a fresh one.
    private var lastAppleAuthorizationCode: String?
    private weak var presentationAnchorView: UIView?

    var displayLabel: String {
        if let email = user?.email, !email.isEmpty { return email }
        if let name = user?.displayName, !name.isEmpty { return name }
        return user?.uid ?? "Signed in"
    }

    /// True when Firebase has an iOS OAuth client ID available (required for Google Sign-In).
    /// This comes from a fully-populated `GoogleService-Info.plist` after enabling Google in Firebase Auth.
    var isGoogleSignInConfigured: Bool {
        guard let clientID = FirebaseApp.app()?.options.clientID else { return false }
        let trimmed = clientID.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return false }
        // Defensive: avoid treating placeholder strings as configured.
        return !trimmed.localizedCaseInsensitiveContains("replace")
    }

    override init() {
        super.init()
        syncFromFirebase()
        authListener = Auth.auth().addStateDidChangeListener { [weak self] _, user in
            Task { @MainActor in
                self?.user = user
                self?.isSignedIn = user != nil
                if user != nil { self?.authError = nil }
            }
        }
    }

    func authInjectionJSON() -> String {
        let signedIn = isSignedIn
        let email = jsonEscape(user?.email ?? "")
        let uid = jsonEscape(user?.uid ?? "")
        let displayName = jsonEscape(user?.displayName ?? "")
        return """
        {"signedIn":\(signedIn),"email":"\(email)","uid":"\(uid)","displayName":"\(displayName)"}
        """
    }

    func injectAuth(into webView: WKWebView?) {
        guard let webView else { return }
        presentationAnchorView = webView
        // The notify call is guarded because this also runs before journal.js
        // has parsed, on the document-start injection path.
        let script = """
        window.__PARLANCE_AUTH__ = \(authInjectionJSON());
        window.__parlanceAuthChanged && window.__parlanceAuthChanged();
        """
        webView.evaluateJavaScript(script, completionHandler: nil)
    }

    func setPresentationAnchor(_ view: UIView?) {
        presentationAnchorView = view
    }

    @discardableResult
    func refreshIDToken() async throws -> String {
        guard let currentUser = Auth.auth().currentUser else {
            throw AuthManagerError.missingIDToken
        }
        return try await currentUser.getIDToken(forcingRefresh: false)
    }

    func signInWithGoogle() async throws {
        authError = nil
        guard let clientID = FirebaseApp.app()?.options.clientID else {
            authError = AuthManagerError.missingGoogleClientID.localizedDescription
            throw AuthManagerError.missingGoogleClientID
        }
        GIDSignIn.sharedInstance.configuration = GIDConfiguration(clientID: clientID)

        guard let presenter = Self.topViewController(from: presentationAnchorView) else {
            authError = AuthManagerError.noPresenter.localizedDescription
            throw AuthManagerError.noPresenter
        }

        let result = try await GIDSignIn.sharedInstance.signIn(withPresenting: presenter)
        guard let idToken = result.user.idToken?.tokenString else {
            authError = AuthManagerError.missingIDToken.localizedDescription
            throw AuthManagerError.missingIDToken
        }

        let credential = GoogleAuthProvider.credential(
            withIDToken: idToken,
            accessToken: result.user.accessToken.tokenString
        )
        _ = try await Auth.auth().signIn(with: credential)
    }

    func signInWithApple() async throws {
        try await runAppleAuthorization(flow: .signIn)
    }

    private func runAppleAuthorization(flow: AppleFlow) async throws {
        authError = nil
        appleFlow = flow
        let nonce = randomNonceString()
        currentNonce = nonce

        let provider = ASAuthorizationAppleIDProvider()
        let request = provider.createRequest()
        request.requestedScopes = [.fullName, .email]
        request.nonce = sha256(nonce)

        do {
            try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
                self.appleSignInContinuation = continuation
                let controller = ASAuthorizationController(authorizationRequests: [request])
                controller.delegate = self
                controller.presentationContextProvider = self
                self.appleSignInController = controller
                controller.performRequests()
            }
        } catch {
            appleSignInController = nil
            let ns = error as NSError
            if ns.domain == ASAuthorizationError.errorDomain,
               ns.code == ASAuthorizationError.canceled.rawValue {
                throw AuthManagerError.cancelled
            }
            authError = error.localizedDescription
            throw error
        }
    }

    func signOut() throws {
        try Auth.auth().signOut()
        GIDSignIn.sharedInstance.signOut()
        authError = nil
    }

    // MARK: - Account deletion (App Store guideline 5.1.1(v))

    /// Permanently deletes the signed-in account: server records first (the
    /// callable needs a live ID token), then the Firebase Auth user itself.
    ///
    /// Reauthentication is unconditional rather than a retry after
    /// `requiresRecentLogin`: Apple's token revocation needs a fresh
    /// authorization code, which only an authorization can produce.
    func deleteAccount() async throws {
        guard let user = Auth.auth().currentUser else {
            throw AuthManagerError.notSignedIn
        }
        authError = nil

        let providers = Set(user.providerData.map(\.providerID))

        if providers.contains("apple.com") {
            try await runAppleAuthorization(flow: .reauthenticate)
        } else if providers.contains("google.com") {
            try await reauthenticateWithGoogle()
        }

        try await deleteServerData()

        if providers.contains("apple.com"), let code = lastAppleAuthorizationCode {
            do {
                try await Auth.auth().revokeToken(withAuthorizationCode: code)
            } catch {
                // Revocation is best effort: the account still has to go away,
                // and a stale code must not strand the user in a half-deleted
                // state with their Firestore records already gone.
                print("[Auth] Apple token revoke failed:", error)
            }
        }

        // Re-resolve rather than reusing the value captured before the
        // reauthentication awaits: `User` is not Sendable, so handing the older
        // reference to an async call trips Swift 6 sending diagnostics.
        guard let userToDelete = Auth.auth().currentUser else {
            throw AuthManagerError.notSignedIn
        }

        do {
            try await userToDelete.delete()
        } catch {
            authError = error.localizedDescription
            throw error
        }

        lastAppleAuthorizationCode = nil
        GIDSignIn.sharedInstance.signOut()
        try? Auth.auth().signOut()
        self.user = nil
        isSignedIn = false
        authError = nil
    }

    /// Wipes `users/{uid}`, `usage/*`, and `packs/*`. Firestore rules block all
    /// client writes to those paths, so this has to run with the Admin SDK.
    private func deleteServerData() async throws {
        let callable = Functions.functions().httpsCallable("deleteAccountData")
        do {
            _ = try await callable.call([:])
        } catch {
            print("[Auth] deleteAccountData failed:", error)
            authError = AuthManagerError.serverDataDeleteFailed.localizedDescription
            throw AuthManagerError.serverDataDeleteFailed
        }
    }

    private func reauthenticateWithGoogle() async throws {
        guard let user = Auth.auth().currentUser else {
            throw AuthManagerError.notSignedIn
        }
        guard let clientID = FirebaseApp.app()?.options.clientID else {
            throw AuthManagerError.missingGoogleClientID
        }
        GIDSignIn.sharedInstance.configuration = GIDConfiguration(clientID: clientID)

        guard let presenter = Self.topViewController(from: presentationAnchorView) else {
            throw AuthManagerError.noPresenter
        }

        do {
            let result = try await GIDSignIn.sharedInstance.signIn(withPresenting: presenter)
            guard let idToken = result.user.idToken?.tokenString else {
                throw AuthManagerError.missingIDToken
            }
            let credential = GoogleAuthProvider.credential(
                withIDToken: idToken,
                accessToken: result.user.accessToken.tokenString
            )
            _ = try await user.reauthenticate(with: credential)
        } catch {
            let ns = error as NSError
            if ns.domain == kGIDSignInErrorDomain,
               ns.code == GIDSignInError.canceled.rawValue {
                throw AuthManagerError.cancelled
            }
            authError = error.localizedDescription
            throw error
        }
    }

    // MARK: - Private

    private func syncFromFirebase() {
        user = Auth.auth().currentUser
        isSignedIn = user != nil
    }

    private static func topViewController(from anchor: UIView? = nil) -> UIViewController? {
        if let anchor {
            var responder: UIResponder? = anchor
            while let next = responder {
                if let viewController = next as? UIViewController {
                    var top = viewController
                    while let presented = top.presentedViewController {
                        top = presented
                    }
                    return top
                }
                responder = next.next
            }
            if let window = anchor.window,
               let root = window.rootViewController {
                var top = root
                while let presented = top.presentedViewController {
                    top = presented
                }
                return top
            }
        }

        guard let window = presentationWindow(), let root = window.rootViewController else { return nil }

        var top = root
        while let presented = top.presentedViewController {
            top = presented
        }
        return top
    }

    /// Resolve a live window for the Apple/Google sign-in sheet. iPadOS 26 ignores
    /// `UIRequiresFullScreen` and can run this app in a resizable/windowed scene, so
    /// `activationState`/`isKeyWindow` are less reliable than before — fall through
    /// several strategies rather than trusting a single one, and never force-unwrap.
    private static func presentationWindow(from anchor: UIView? = nil) -> UIWindow? {
        if let window = anchor?.window, window.windowScene != nil { return window }

        if let scene = anchor?.window?.windowScene {
            if let key = scene.windows.first(where: \.isKeyWindow) { return key }
            if let visible = scene.windows.first(where: { !$0.isHidden }) { return visible }
            if let any = scene.windows.first { return any }
        }

        let windowScenes = UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }

        if let scene = windowScenes.first(where: { $0.activationState == .foregroundActive }),
           let key = scene.windows.first(where: \.isKeyWindow) {
            return key
        }

        // Fall back across ALL scenes (not just foregroundActive — under iPadOS 26's
        // windowing model a scene hosting our content may not report that state
        // promptly), preferring any key window, then any visible window.
        if let key = windowScenes.flatMap(\.windows).first(where: \.isKeyWindow) {
            return key
        }
        if let visible = windowScenes.flatMap(\.windows).first(where: { !$0.isHidden }) {
            return visible
        }
        return windowScenes.flatMap(\.windows).first
    }

    private func jsonEscape(_ value: String) -> String {
        value
            .replacingOccurrences(of: "\\", with: "\\\\")
            .replacingOccurrences(of: "\"", with: "\\\"")
            .replacingOccurrences(of: "\n", with: "\\n")
            .replacingOccurrences(of: "\r", with: "\\r")
    }

    private func randomNonceString(length: Int = 32) -> String {
        precondition(length > 0)
        var randomBytes = [UInt8](repeating: 0, count: length)
        let errorCode = SecRandomCopyBytes(kSecRandomDefault, randomBytes.count, &randomBytes)
        if errorCode != errSecSuccess {
            fatalError("Unable to generate nonce. SecRandomCopyBytes failed with OSStatus \(errorCode)")
        }
        let charset: [Character] = Array("0123456789ABCDEFGHIJKLMNOPQRSTUVXYZabcdefghijklmnopqrstuvwxyz-._")
        return String(randomBytes.map { charset[Int($0) % charset.count] })
    }

    private func sha256(_ input: String) -> String {
        let inputData = Data(input.utf8)
        let hashed = SHA256.hash(data: inputData)
        return hashed.compactMap { String(format: "%02x", $0) }.joined()
    }
}

// MARK: - Apple Sign In

extension AuthManager: ASAuthorizationControllerDelegate, ASAuthorizationControllerPresentationContextProviding {

    func presentationAnchor(for controller: ASAuthorizationController) -> ASPresentationAnchor {
        if let window = Self.presentationWindow(from: presentationAnchorView) {
            return window
        }
        // Last resort: a fresh, attached window from the app's own scene rather than
        // force-unwrapping into a crash if every other lookup came up empty.
        if let scene = UIApplication.shared.connectedScenes.compactMap({ $0 as? UIWindowScene }).first {
            return UIWindow(windowScene: scene)
        }
        return UIWindow(frame: UIScreen.main.bounds)
    }

    func authorizationController(controller: ASAuthorizationController,
                                 didCompleteWithAuthorization authorization: ASAuthorization) {
        guard let appleIDCredential = authorization.credential as? ASAuthorizationAppleIDCredential,
              let nonce = currentNonce,
              let appleTokenData = appleIDCredential.identityToken,
              let idTokenString = String(data: appleTokenData, encoding: .utf8)
        else {
            appleSignInContinuation?.resume(throwing: AuthManagerError.missingIDToken)
            appleSignInContinuation = nil
            appleSignInController = nil
            currentNonce = nil
            return
        }

        let credential = OAuthProvider.appleCredential(
            withIDToken: idTokenString,
            rawNonce: nonce,
            fullName: appleIDCredential.fullName
        )

        if let codeData = appleIDCredential.authorizationCode,
           let code = String(data: codeData, encoding: .utf8) {
            lastAppleAuthorizationCode = code
        } else {
            lastAppleAuthorizationCode = nil
        }

        let flow = appleFlow

        Task { @MainActor in
            defer {
                appleSignInContinuation = nil
                appleSignInController = nil
                currentNonce = nil
                appleFlow = .signIn
            }

            do {
                switch flow {
                case .signIn:
                    _ = try await Auth.auth().signIn(with: credential)
                case .reauthenticate:
                    guard let user = Auth.auth().currentUser else {
                        throw AuthManagerError.notSignedIn
                    }
                    _ = try await user.reauthenticate(with: credential)
                }
                appleSignInContinuation?.resume()
            } catch {
                authError = error.localizedDescription
                appleSignInContinuation?.resume(throwing: error)
            }
        }
    }

    func authorizationController(controller: ASAuthorizationController, didCompleteWithError error: Error) {
        defer {
            appleSignInContinuation = nil
            appleSignInController = nil
            currentNonce = nil
            appleFlow = .signIn
        }
        let ns = error as NSError
        if ns.domain == ASAuthorizationError.errorDomain,
           ns.code == ASAuthorizationError.canceled.rawValue {
            appleSignInContinuation?.resume(throwing: AuthManagerError.cancelled)
        } else {
            authError = error.localizedDescription
            appleSignInContinuation?.resume(throwing: error)
        }
    }
}
