import Combine
import Foundation
import StoreKit

/// StoreKit 2 for Parlance Plus and the local feedback pack.
/// Entitlement is the App Store receipt. There is no Cloud Functions grant.
@MainActor
final class StoreKitManager: ObservableObject {

    static let shared = StoreKitManager()

    // MARK: - Product IDs

    static let callPack100 = "com.parlance.interpreterguide.callpack100"
    static let plusMonthly = "com.parlance.interpreterguide.plusmonthly"
    static let feedbackPack15 = "com.parlance.interpreterguide.feedbackpack15"
    private static let allProductIDs: Set<String> = [plusMonthly, feedbackPack15]

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
    /// Set when a feedback-pack transaction is finished so the web layer can
    /// credit 15 analyses once per App Store transaction id.
    @Published private(set) var lastPackCreditTransactionId: String?

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

    var isFeedbackPackPurchasable: Bool {
        products.contains { $0.id == Self.feedbackPack15 }
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
                await transaction.finish()
                creditPackIfNeeded(transaction)
                await refreshPlusEntitlement()
                return .success(transactionId: String(transaction.id))

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

    func purchaseFeedbackPack() async -> PurchaseResult {
        guard let product = products.first(where: { $0.id == Self.feedbackPack15 }) else {
            await loadProducts()
            guard let product = products.first(where: { $0.id == Self.feedbackPack15 }) else {
                return .failed(unavailableMessage())
            }
            return await purchase(product)
        }
        return await purchase(product)
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
                    await transaction.finish()
                    self.creditPackIfNeeded(transaction)
                    await self.refreshPlusEntitlement()
                } catch {
                    print("[StoreKit] Unverified transaction:", error)
                }
            }
        }
    }

    private static let creditedPackTxKey = "parlance_credited_pack_tx"

    private func creditPackIfNeeded(_ transaction: Transaction) {
        guard transaction.productID == Self.feedbackPack15 else { return }
        let id = String(transaction.id)
        var credited = UserDefaults.standard.stringArray(forKey: Self.creditedPackTxKey) ?? []
        if credited.contains(id) { return }
        credited.append(id)
        UserDefaults.standard.set(Array(credited.suffix(50)), forKey: Self.creditedPackTxKey)
        lastPackCreditTransactionId = id
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

    var feedbackPackDisplayPrice: String? {
        products.first(where: { $0.id == Self.feedbackPack15 })?.displayPrice
    }
}
