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
    private static let allProductIDs: Set<String> = [callPack100]

    // MARK: - Published state

    @Published private(set) var products: [Product] = []
    @Published private(set) var isPurchasing = false
    @Published private(set) var purchaseError: String?

    // MARK: - Internal

    private var transactionListenerTask: Task<Void, Never>?

    private init() {
        transactionListenerTask = listenForTransactions()
        Task { await loadProducts() }
    }

    deinit {
        transactionListenerTask?.cancel()
    }

    // MARK: - Load products

    func loadProducts() async {
        do {
            let fetched = try await Product.products(for: Self.allProductIDs)
            products = fetched.sorted { $0.price < $1.price }
        } catch {
            print("[StoreKit] Failed to load products:", error)
        }
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
                return .failed("Product unavailable. Check your connection and try again.")
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
                let grantResult = await grantPackOnServer(
                    transaction: transaction,
                    signedTransactionInfo: verification.jwsRepresentation
                )
                if case .success = grantResult {
                    await transaction.finish()
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

    // MARK: - Transaction listener

    private func listenForTransactions() -> Task<Void, Never> {
        Task(priority: .background) { [weak self] in
            for await result in Transaction.updates {
                guard let self else { return }
                do {
                    let transaction = try self.checkVerified(result)
                    let grantResult = await self.grantPackOnServer(
                        transaction: transaction,
                        signedTransactionInfo: result.jwsRepresentation
                    )
                    if case .success = grantResult {
                        await transaction.finish()
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
}
