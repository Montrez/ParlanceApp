package com.parlance.interpreterguide;

import android.app.Activity;
import android.util.Log;

import androidx.annotation.Nullable;

import com.android.billingclient.api.AcknowledgePurchaseParams;
import com.android.billingclient.api.BillingClient;
import com.android.billingclient.api.BillingClientStateListener;
import com.android.billingclient.api.BillingFlowParams;
import com.android.billingclient.api.BillingResult;
import com.android.billingclient.api.PendingPurchasesParams;
import com.android.billingclient.api.ProductDetails;
import com.android.billingclient.api.Purchase;
import com.android.billingclient.api.PurchasesUpdatedListener;
import com.android.billingclient.api.QueryProductDetailsParams;
import com.android.billingclient.api.QueryPurchasesParams;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * Android counterpart to {@code StoreKitManager.swift}. Same product IDs,
 * same Plus / call-pack split, same local entitlement for medical and legal
 * guides. Play Billing is the store; the web layer only sees config flags.
 */
public class ParlanceBilling implements PurchasesUpdatedListener {

    private static final String TAG = "ParlanceBilling";
    // Play product IDs cannot use the iOS reverse-DNS form.
    static final String PLUS_MONTHLY = "plusmonthly";
    static final String CALL_PACK_100 = "callpack100";

    interface Listener {
        void onBillingChanged();
    }

    interface PurchaseCallback {
        void onResult(@Nullable String transactionId, @Nullable String error);
    }

    private final Activity activity;
    private final BillingClient client;
    private Listener listener;
    private PurchaseCallback pendingCallback;
    private String pendingProductId;

    private final List<ProductDetails> products = new CopyOnWriteArrayList<>();
    private volatile boolean plusActive;
    private volatile boolean plusPurchasable;
    private volatile String plusPrice;
    private volatile boolean ready;

    public ParlanceBilling(Activity activity) {
        this.activity = activity;
        this.client = BillingClient.newBuilder(activity)
                .setListener(this)
                .enablePendingPurchases(
                        PendingPurchasesParams.newBuilder().enableOneTimeProducts().build())
                .build();
        connect();
    }

    public void setListener(Listener listener) {
        this.listener = listener;
        if (listener != null) listener.onBillingChanged();
    }

    public boolean isPlusActive() {
        return plusActive;
    }

    public boolean isPlusPurchasable() {
        return plusPurchasable;
    }

    @Nullable
    public String plusMonthlyDisplayPrice() {
        return plusPrice;
    }

    public boolean isReady() {
        return ready;
    }

    public void purchasePlus(PurchaseCallback callback) {
        launch(PLUS_MONTHLY, BillingClient.ProductType.SUBS, callback);
    }

    public void purchaseCallPack(PurchaseCallback callback) {
        launch(CALL_PACK_100, BillingClient.ProductType.INAPP, callback);
    }

    public void restorePlus(PurchaseCallback callback) {
        queryPurchases(() -> {
            if (callback != null) {
                callback.onResult(plusActive ? "restored" : null, null);
            }
            notifyChanged();
        });
    }

    private void connect() {
        client.startConnection(new BillingClientStateListener() {
            @Override
            public void onBillingSetupFinished(BillingResult result) {
                if (result.getResponseCode() != BillingClient.BillingResponseCode.OK) {
                    Log.w(TAG, "Billing setup failed: " + result.getDebugMessage());
                    ready = true;
                    notifyChanged();
                    return;
                }
                queryProducts();
                queryPurchases(() -> {
                    ready = true;
                    notifyChanged();
                });
            }

            @Override
            public void onBillingServiceDisconnected() {
                connect();
            }
        });
    }

    private void queryProducts() {
        // Only query products that exist in Play Console. A missing INAPP id
        // in the same request can empty the whole catalog, which hides Plus.
        List<QueryProductDetailsParams.Product> list = new ArrayList<>();
        list.add(QueryProductDetailsParams.Product.newBuilder()
                .setProductId(PLUS_MONTHLY)
                .setProductType(BillingClient.ProductType.SUBS)
                .build());
        client.queryProductDetailsAsync(
                QueryProductDetailsParams.newBuilder().setProductList(list).build(),
                (result, details) -> {
                    if (result.getResponseCode() != BillingClient.BillingResponseCode.OK) {
                        Log.w(TAG, "Product query failed: " + result.getDebugMessage());
                        plusPurchasable = false;
                        notifyChanged();
                        return;
                    }
                    products.clear();
                    products.addAll(details);
                    plusPurchasable = findProduct(PLUS_MONTHLY) != null;
                    plusPrice = formattedPrice(findProduct(PLUS_MONTHLY));
                    if (!plusPurchasable) {
                        Log.w(TAG, "plusmonthly not in Play catalog. details=" + details.size());
                    }
                    notifyChanged();
                });
    }

    private void queryPurchases(Runnable done) {
        client.queryPurchasesAsync(
                QueryPurchasesParams.newBuilder()
                        .setProductType(BillingClient.ProductType.SUBS)
                        .build(),
                (result, purchases) -> {
                    boolean active = false;
                    if (result.getResponseCode() == BillingClient.BillingResponseCode.OK) {
                        for (Purchase purchase : purchases) {
                            if (purchase.getPurchaseState() != Purchase.PurchaseState.PURCHASED) {
                                continue;
                            }
                            acknowledge(purchase);
                            if (purchase.getProducts().contains(PLUS_MONTHLY)) {
                                active = true;
                            }
                        }
                    }
                    plusActive = active;
                    if (done != null) done.run();
                    else notifyChanged();
                });
    }

    private void launch(String productId, String type, PurchaseCallback callback) {
        ProductDetails details = findProduct(productId);
        if (details == null) {
            queryProducts();
            if (callback != null) {
                callback.onResult(null, "This purchase is not available right now. Try again later.");
            }
            return;
        }
        BillingFlowParams.ProductDetailsParams.Builder item =
                BillingFlowParams.ProductDetailsParams.newBuilder().setProductDetails(details);
        if (BillingClient.ProductType.SUBS.equals(type)) {
            String offer = offerToken(details);
            if (offer == null) {
                if (callback != null) {
                    callback.onResult(null, "This purchase is not available right now. Try again later.");
                }
                return;
            }
            item.setOfferToken(offer);
        }
        pendingCallback = callback;
        pendingProductId = productId;
        BillingResult result = client.launchBillingFlow(
                activity,
                BillingFlowParams.newBuilder()
                        .setProductDetailsParamsList(Collections.singletonList(item.build()))
                        .build());
        if (result.getResponseCode() != BillingClient.BillingResponseCode.OK) {
            pendingCallback = null;
            pendingProductId = null;
            if (callback != null) {
                callback.onResult(null, result.getDebugMessage());
            }
        }
    }

    @Override
    public void onPurchasesUpdated(BillingResult result, @Nullable List<Purchase> purchases) {
        PurchaseCallback callback = pendingCallback;
        pendingCallback = null;
        String wanted = pendingProductId;
        pendingProductId = null;

        if (result.getResponseCode() == BillingClient.BillingResponseCode.USER_CANCELED) {
            if (callback != null) callback.onResult(null, "cancelled");
            return;
        }
        if (result.getResponseCode() != BillingClient.BillingResponseCode.OK || purchases == null) {
            if (callback != null) {
                String msg = result.getDebugMessage();
                callback.onResult(null, msg == null || msg.isEmpty()
                        ? "Purchase failed." : msg);
            }
            return;
        }
        String transactionId = null;
        for (Purchase purchase : purchases) {
            if (purchase.getPurchaseState() != Purchase.PurchaseState.PURCHASED) continue;
            acknowledge(purchase);
            if (purchase.getProducts().contains(PLUS_MONTHLY)) {
                plusActive = true;
            }
            if (wanted == null || purchase.getProducts().contains(wanted)) {
                transactionId = purchase.getOrderId();
                if (transactionId == null || transactionId.isEmpty()) {
                    transactionId = purchase.getPurchaseToken();
                }
            }
        }
        notifyChanged();
        if (callback != null) callback.onResult(transactionId, null);
    }

    private void acknowledge(Purchase purchase) {
        if (purchase.isAcknowledged()) return;
        client.acknowledgePurchase(
                AcknowledgePurchaseParams.newBuilder()
                        .setPurchaseToken(purchase.getPurchaseToken())
                        .build(),
                result -> {
                    if (result.getResponseCode() != BillingClient.BillingResponseCode.OK) {
                        Log.w(TAG, "Acknowledge failed: " + result.getDebugMessage());
                    }
                });
    }

    @Nullable
    private ProductDetails findProduct(String id) {
        for (ProductDetails details : products) {
            if (id.equals(details.getProductId())) return details;
        }
        return null;
    }

    @Nullable
    private static String offerToken(ProductDetails details) {
        List<ProductDetails.SubscriptionOfferDetails> offers = details.getSubscriptionOfferDetails();
        if (offers == null || offers.isEmpty()) return null;
        for (ProductDetails.SubscriptionOfferDetails offer : offers) {
            if ("plus-monthly".equals(offer.getBasePlanId())) {
                return offer.getOfferToken();
            }
        }
        return offers.get(0).getOfferToken();
    }

    @Nullable
    private static String formattedPrice(ProductDetails details) {
        if (details == null) return null;
        if (BillingClient.ProductType.SUBS.equals(details.getProductType())) {
            List<ProductDetails.SubscriptionOfferDetails> offers = details.getSubscriptionOfferDetails();
            if (offers == null || offers.isEmpty()) return null;
            ProductDetails.SubscriptionOfferDetails chosen = offers.get(0);
            for (ProductDetails.SubscriptionOfferDetails offer : offers) {
                if ("plus-monthly".equals(offer.getBasePlanId())) {
                    chosen = offer;
                    break;
                }
            }
            List<ProductDetails.PricingPhase> phases =
                    chosen.getPricingPhases().getPricingPhaseList();
            if (phases.isEmpty()) return null;
            return phases.get(0).getFormattedPrice();
        }
        ProductDetails.OneTimePurchaseOfferDetails one = details.getOneTimePurchaseOfferDetails();
        return one == null ? null : one.getFormattedPrice();
    }

    private void notifyChanged() {
        Listener next = listener;
        if (next != null) {
            activity.runOnUiThread(next::onBillingChanged);
        }
    }
}
