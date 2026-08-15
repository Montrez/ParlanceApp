import Combine
import FirebaseFunctions
import Foundation
import StoreKit

/// Manages StoreKit 2 purchases for Parlance call packs.
@MainActor
final class StoreKitManager: ObservableObject {

    static let shared = StoreKitManager()

    // MARK: - Product IDs

    static let callPack100 = "com.parlance.interpreterguide.callpack100"
    static let plusMonthly = "com.parlance.interpreterguide.plusmonthly"
    private static let allProductIDs: Set<String> = [callPack100, plusMonthly]

    // MARK: - Published state

    @Published private(set) var products: [Product] = []
    @Published private(set) var isPurchasing = false
    @Published private(set) var purchaseError: String?
    /// Local, verified entitlement check via Transaction.currentEntitlements —
    /// gates client-only features (medical/legal guides) without a server round trip.
    @Published private(set) var isPlusActive = false
    /// Last `Product.products(for:)` failure, if any. An empty catalog and a
    /// failed fetch look identical to callers otherwise, and they need very
    /// different fixes (App Store Connect setup vs. retry).
    @Published private(set) var productLoadError: String?
    /// False until the first catalog fetch finishes, so the paywall can wait
    /// instead of claiming the subscription is unavailable during launch.
    @Published private(set) var didAttemptProductLoad = false

    // MARK: - Internal

    private var transactionListenerTask: Task<Void, Never>?

    private init() {
        transactionListenerTask = listenForTransactions()
        Task {
            await loadProducts()
            await refreshPlusEntitlement()
        }
    }

    deinit {
        transactionListenerTask?.cancel()
    }

    // MARK: - Load products

    func loadProducts() async {
        do {
            let fetched = try await Product.products(for: Self.allProductIDs)
            products = fetched.sorted { $0.price < $1.price }
            productLoadError = nil
            if fetched.isEmpty {
                print("[StoreKit] App Store returned no products for \(Self.allProductIDs)")
            }
        } catch {
            productLoadError = error.localizedDescription
            print("[StoreKit] Failed to load products:", error)
        }
        didAttemptProductLoad = true
    }

    /// True once the App Store has actually returned the subscription. The
    /// paywall keys its Subscribe button off this so the button is never live
    /// when a tap could only ever fail.
    var isPlusPurchasable: Bool {
        products.contains { $0.id == Self.plusMonthly }
    }

    var isCallPackPurchasable: Bool {
        products.contains { $0.id == Self.callPack100 }
    }

    /// Distinguishes "the App Store call failed" from "the App Store answered
    /// but this product is not in the catalog", which is an App Store Connect
    /// configuration problem the user can do nothing about.
    private func unavailableMessage() -> String {
        if let productLoadError {
            return "Could not reach the App Store (\(productLoadError)). Check your connection and try again."
        }
        return "This purchase isn't available right now. Please try again later."
    }

    // MARK: - Purchase

    enum PurchaseResult {
        case success(transactionId: String)
        case cancelled
        case failed(String)
    }

    func purchaseCallPack() async -> PurchaseResult {
        guard let product = products.first(where: { $0.id == Self.callPack100 }) else {
            await loadProducts()
            guard let product = products.first(where: { $0.id == Self.callPack100 }) else {
                return .failed(unavailableMessage())
            }
            return await purchase(product)
        }
        return await purchase(product)
    }

    private func purchase(_ product: Product) async -> PurchaseResult {
        isPurchasing = true
        purchaseError = nil
        defer { isPurchasing = false }

        do {
            let result = try await product.purchase()
            switch result {
            case .success(let verification):
                let transaction = try checkVerified(verification)
                let grantResult: PurchaseResult
                if transaction.productID == Self.plusMonthly {
                    grantResult = await grantPlusOnServer(
                        transaction: transaction,
                        signedTransactionInfo: verification.jwsRepresentation
                    )
                } else {
                    grantResult = await grantPackOnServer(
                        transaction: transaction,
                        signedTransactionInfo: verification.jwsRepresentation
                    )
                }
                if case .success = grantResult {
                    await transaction.finish()
                    await refreshPlusEntitlement()
                }
                return grantResult

            case .userCancelled:
                return .cancelled

            case .pending:
                return .failed("Purchase is pending approval. Check back shortly.")

            @unknown default:
                return .failed("Unexpected purchase state.")
            }
        } catch {
            let msg = error.localizedDescription
            purchaseError = msg
            return .failed(msg)
        }
    }

    func purchasePlus() async -> PurchaseResult {
        guard let product = products.first(where: { $0.id == Self.plusMonthly }) else {
            await loadProducts()
            guard let product = products.first(where: { $0.id == Self.plusMonthly }) else {
                return .failed(unavailableMessage())
            }
            return await purchase(product)
        }
        return await purchase(product)
    }

    /// Re-syncs with the App Store and re-checks local entitlements. Used for
    /// the "Restore purchase" button — StoreKit subscriptions don't need a
    /// receipt re-download the way old SKPaymentQueue restores did.
    func restorePlus() async -> Bool {
        do {
            try await AppStore.sync()
        } catch {
            print("[StoreKit] AppStore.sync failed:", error)
        }
        await refreshPlusEntitlement()
        return isPlusActive
    }

    /// Scans verified, current entitlements for an active Plus subscription.
    /// This is the local source of truth for gating bundled content — it
    /// reflects cancellations/expirations automatically via StoreKit.
    func refreshPlusEntitlement() async {
        var active = false
        for await result in Transaction.currentEntitlements {
            guard case .verified(let transaction) = result else { continue }
            if transaction.productID == Self.plusMonthly && transaction.revocationDate == nil {
                active = true
            }
        }
        isPlusActive = active
    }

    // MARK: - Transaction listener

    private func listenForTransactions() -> Task<Void, Never> {
        Task(priority: .background) { [weak self] in
            for await result in Transaction.updates {
                guard let self else { return }
                do {
                    let transaction = try self.checkVerified(result)
                    let grantResult: PurchaseResult
                    if transaction.productID == Self.plusMonthly {
                        grantResult = await self.grantPlusOnServer(
                            transaction: transaction,
                            signedTransactionInfo: result.jwsRepresentation
                        )
                    } else {
                        grantResult = await self.grantPackOnServer(
                            transaction: transaction,
                            signedTransactionInfo: result.jwsRepresentation
                        )
                    }
                    if case .success = grantResult {
                        await transaction.finish()
                        await self.refreshPlusEntitlement()
                    }
                } catch {
                    print("[StoreKit] Unverified transaction:", error)
                }
            }
        }
    }

    // MARK: - Server grant

    private func grantPackOnServer(
        transaction: Transaction,
        signedTransactionInfo: String
    ) async -> PurchaseResult {
        let transactionId = String(transaction.id)
        let callable = Functions.functions().httpsCallable("grantCallPack")
        do {
            let result = try await callable.call([
                "signedTransactionInfo": signedTransactionInfo,
                "transactionId": transactionId,
                "productId": transaction.productID,
            ])
            if let data = result.data as? [String: Any] {
                let remaining = data["remaining"] as? Int ?? 100
                print("[StoreKit] Pack granted. Remaining calls: \(remaining)")
            }
            return .success(transactionId: transactionId)
        } catch {
            print("[StoreKit] grantCallPack cloud error:", error)
            return .failed("Purchase completed, but crediting calls failed. Restart the app to retry, or contact support.")
        }
    }

    /// Registers the subscription server-side so unlimited-usage checks in
    /// Firebase Functions (`usage.js` "plus" tier) see the same entitlement
    /// as the local StoreKit check.
    private func grantPlusOnServer(
        transaction: Transaction,
        signedTransactionInfo: String
    ) async -> PurchaseResult {
        let transactionId = String(transaction.id)
        let callable = Functions.functions().httpsCallable("grantPlusSubscription")
        do {
            let result = try await callable.call([
                "signedTransactionInfo": signedTransactionInfo,
                "transactionId": transactionId,
                "productId": transaction.productID,
            ])
            if let data = result.data as? [String: Any] {
                let tier = data["tier"] as? String ?? "plus"
                print("[StoreKit] Plus granted. Tier: \(tier)")
            }
            return .success(transactionId: transactionId)
        } catch {
            print("[StoreKit] grantPlusSubscription cloud error:", error)
            // Local entitlement (refreshPlusEntitlement) still unlocks bundled
            // content even if the server sync fails — only the unlimited-AI-calls
            // perk depends on the server tier, and that will retry on next launch.
            return .success(transactionId: transactionId)
        }
    }

    // MARK: - Verification

    private func checkVerified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .unverified(_, let error):
            throw error
        case .verified(let value):
            return value
        }
    }

    // MARK: - Formatted price helper

    var callPackDisplayPrice: String {
        products.first(where: { $0.id == Self.callPack100 })?.displayPrice ?? "$0.99"
    }

    var plusMonthlyDisplayPrice: String? {
        products.first(where: { $0.id == Self.plusMonthly })?.displayPrice
    }
}
