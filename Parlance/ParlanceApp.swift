import FirebaseCore
import SwiftUI

@main
struct ParlanceApp: App {
    @State private var authManager: AuthManager

    init() {
        FirebaseApp.configure()
        _authManager = State(initialValue: AuthManager.shared)
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(authManager)
                .ignoresSafeArea()
        }
    }
}
