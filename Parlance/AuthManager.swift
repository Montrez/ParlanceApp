import AuthenticationServices
import CryptoKit
import FirebaseAuth
import FirebaseCore
import GoogleSignIn
import Observation
import UIKit
import WebKit

enum AuthManagerError: LocalizedError {
    case cancelled
    case missingGoogleClientID
    case noPresenter
    case missingIDToken

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

    private var authListener: AuthStateDidChangeListenerHandle?
    private var currentNonce: String?
    private var appleSignInContinuation: CheckedContinuation<Void, Error>?

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
        let script = "window.__PARLANCE_AUTH__ = \(authInjectionJSON());"
        webView.evaluateJavaScript(script, completionHandler: nil)
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

        guard let presenter = Self.topViewController() else {
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
        authError = nil
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
                controller.performRequests()
            }
        } catch {
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

    // MARK: - Private

    private func syncFromFirebase() {
        user = Auth.auth().currentUser
        isSignedIn = user != nil
    }

    private static func topViewController() -> UIViewController? {
        guard let scene = UIApplication.shared.connectedScenes
            .compactMap({ $0 as? UIWindowScene })
            .first(where: { $0.activationState == .foregroundActive }),
              let root = scene.windows.first(where: \.isKeyWindow)?.rootViewController
        else { return nil }

        var top = root
        while let presented = top.presentedViewController {
            top = presented
        }
        return top
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
        UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap(\.windows)
            .first(where: \.isKeyWindow)
            ?? UIApplication.shared.connectedScenes
                .compactMap { $0 as? UIWindowScene }
                .flatMap(\.windows)
                .first!
    }

    func authorizationController(controller: ASAuthorizationController,
                                 didCompleteWithAuthorization authorization: ASAuthorization) {
        defer { appleSignInContinuation = nil }

        guard let appleIDCredential = authorization.credential as? ASAuthorizationAppleIDCredential,
              let nonce = currentNonce,
              let appleTokenData = appleIDCredential.identityToken,
              let idTokenString = String(data: appleTokenData, encoding: .utf8)
        else {
            appleSignInContinuation?.resume(throwing: AuthManagerError.missingIDToken)
            return
        }

        let credential = OAuthProvider.appleCredential(
            withIDToken: idTokenString,
            rawNonce: nonce,
            fullName: appleIDCredential.fullName
        )

        Task { @MainActor in
            do {
                _ = try await Auth.auth().signIn(with: credential)
                appleSignInContinuation?.resume()
            } catch {
                authError = error.localizedDescription
                appleSignInContinuation?.resume(throwing: error)
            }
        }
    }

    func authorizationController(controller: ASAuthorizationController, didCompleteWithError error: Error) {
        defer { appleSignInContinuation = nil }
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
