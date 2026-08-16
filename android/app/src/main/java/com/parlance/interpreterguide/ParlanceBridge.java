package com.parlance.interpreterguide;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.util.Log;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;


/**
 * JavaScript bridge for the Parlance web layer, mirroring the iOS
 * WKScriptMessageHandler in {@code Parlance/ContentView.swift}.
 *
 * <p>Message shapes and the {@code window.__parlance*} callbacks are identical
 * on both platforms, so {@code journal.js} never branches on platform. Where the
 * two genuinely differ — Android has no native settings sheet — it is
 * reported through the capability flags in {@link #getConfig()} rather
 * than through platform sniffing. Plus and call packs use Play Billing.
 *
 * <p>iOS injects its globals with a document-start {@code WKUserScript}. Android
 * has no equivalent, so {@link #getConfig()} and {@link #getAuth()} expose the
 * same payloads synchronously and journal.js hydrates from them on load.
 */
public class ParlanceBridge {

    public static final String JS_NAME = "ParlanceNative";
    private static final String TAG = "ParlanceBridge";

    private final Activity activity;
    private final WebView webView;
    private final ParlanceAuth auth;
    private final ParlanceSLMEngine slm;
    private final ParlanceBilling billing;

    public ParlanceBridge(Activity activity, WebView webView) {
        this.activity = activity;
        this.webView = webView;
        this.auth = new ParlanceAuth(activity);
        this.slm = new ParlanceSLMEngine(activity);
        this.slm.setAvailabilityListener(this::publishCoachConfig);
        this.billing = new ParlanceBilling(activity);
        this.billing.setListener(new ParlanceBilling.Listener() {
            @Override
            public void onBillingChanged() {
                publishBillingConfig();
            }

            @Override
            public void onPackCredited(String transactionId) {
                evaluateJs("window.__parlanceCreditFeedbackPack && window.__parlanceCreditFeedbackPack("
                        + quote(transactionId) + ")");
            }
        });
    }

    // MARK: - Synchronous state for hydration

    @JavascriptInterface
    public String getConfig() {
        JSONObject capabilities = new JSONObject();
        JSONObject config = new JSONObject();
        try {
            capabilities.put("nativeAuth", true);
            capabilities.put("inAppPurchase", true);
            // Android uses the web AI settings modal; there is no native sheet.
            capabilities.put("nativeSettings", false);

            config.put("mode", "unified");
            config.put("platform", "android");
            config.put("capabilities", capabilities);
            config.put("onDeviceAvailable", false);
            config.put("groqAvailable", false);
            config.put("coachOnly", true);
            JSONArray coachLangs = new JSONArray();
            for (String lang : slm.availableLanguages()) {
                coachLangs.put(lang);
            }
            config.put("parlanceCoachAvailable", coachLangs.length() > 0);
            config.put("parlanceCoachInstalling", slm.isInstalling());
            config.put("parlanceCoachLanguages", coachLangs);
            config.put("isPlusActive", billing.isPlusActive());
            config.put("plusPurchaseAvailable", billing.isPlusPurchasable());
            config.put("feedbackPackPurchaseAvailable", billing.isFeedbackPackPurchasable());
            config.put("feedbackDebugTools",
                    (activity.getApplicationInfo().flags
                            & android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE) != 0);
            if (billing.plusMonthlyDisplayPrice() != null) {
                config.put("plusMonthlyPriceDisplay", billing.plusMonthlyDisplayPrice());
            }
            if (billing.feedbackPackDisplayPrice() != null) {
                config.put("feedbackPackPriceDisplay", billing.feedbackPackDisplayPrice());
            }
        } catch (JSONException e) {
            Log.e(TAG, "Failed to build config", e);
        }
        return config.toString();
    }

    @JavascriptInterface
    public String getAuth() {
        return auth.authStateJson();
    }

    // MARK: - Message dispatch

    @JavascriptInterface
    public void postMessage(String raw) {
        if (raw == null || raw.isEmpty()) {
            return;
        }
        // iOS accepts bare strings for the two sheet-opening messages; keep the
        // same contract so journal.js can post either shape.
        if (!raw.trim().startsWith("{")) {
            return;
        }

        final JSONObject body;
        try {
            body = new JSONObject(raw);
        } catch (JSONException e) {
            Log.w(TAG, "Ignoring malformed bridge message", e);
            return;
        }

        final String action = body.optString("action", "");
        final String requestId = body.optString("requestId", "");

        activity.runOnUiThread(() -> dispatch(action, requestId, body));
    }

    private void dispatch(String action, String requestId, JSONObject body) {
        switch (action) {
            case "signInGoogle":
                auth.signInWithGoogle(error -> finishAuthAction(requestId, error));
                break;
            case "signInApple":
                auth.signInWithApple(error -> finishAuthAction(requestId, error));
                break;
            case "signOut":
                auth.signOut();
                finishAuthAction(requestId, null);
                break;
            case "deleteAccount":
                auth.deleteAccount(error -> finishAuthAction(requestId, error));
                break;
            case "openURL":
                openUrl(body.optString("url", ""));
                break;
            case "analyzeFirebase":
                analyzeFirebase(requestId, body);
                break;
            case "analyzeParlanceSLM":
                analyzeParlanceSLM(requestId, body);
                break;
            case "unloadParlanceSLM":
                new Thread(slm::unload, "parlance-slm-unload").start();
                break;
            case "purchaseCallPack":
                billing.purchaseCallPack((transactionId, error) ->
                        finishPurchase("window.__parlancePurchaseResult", requestId, transactionId, error));
                break;
            case "purchaseFeedbackPack":
                billing.purchaseFeedbackPack((transactionId, error) ->
                        finishPurchase("window.__parlancePurchaseResult", requestId, transactionId, error));
                break;
            case "purchasePlus":
                billing.purchasePlus((transactionId, error) ->
                        finishPurchase("window.__parlancePlusPurchaseResult", requestId, transactionId, error));
                break;
            case "restorePlus":
                billing.restorePlus((transactionId, error) -> {
                    boolean restored = billing.isPlusActive();
                    evaluateJs("window.__parlancePlusRestoreResult && window.__parlancePlusRestoreResult("
                            + quote(requestId) + ", {restored:" + restored + "}, "
                            + (error == null ? "null" : quote(error)) + ")");
                });
                break;
            default:
                Log.w(TAG, "Unhandled bridge action: " + action);
                break;
        }
    }

    // MARK: - Handlers

    private void openUrl(String url) {
        if (url.isEmpty()) {
            return;
        }
        Uri uri = Uri.parse(url);
        if (!"https".equalsIgnoreCase(uri.getScheme())) {
            return;
        }
        try {
            activity.startActivity(new Intent(Intent.ACTION_VIEW, uri));
        } catch (ActivityNotFoundException e) {
            Log.w(TAG, "No browser available for " + url, e);
        }
    }

    /**
     * Same door as iOS {@code handleParlanceSLMAnalysis}. Inference is off the
     * UI thread; the JS callback is posted back onto the WebView.
     */
    private void analyzeParlanceSLM(String requestId, JSONObject body) {
        final String sentence = body.optString("sentence", "");
        final String language = body.optString("language", "es");
        final String ragContext = body.optString("ragContext", "");
        new Thread(() -> {
            try {
                JSONObject result = slm.analyze(sentence, language, ragContext);
                evaluateJs("window.__parlanceSLMResult && window.__parlanceSLMResult("
                        + quote(requestId) + ", " + result.toString() + ", null)");
            } catch (Exception error) {
                evaluateJs("window.__parlanceSLMResult && window.__parlanceSLMResult("
                        + quote(requestId) + ", null, " + quote(describe(error)) + ")");
            }
        }, "parlance-slm").start();
    }

    private void analyzeFirebase(String requestId, JSONObject body) {
        evaluateJs("window.__parlanceFirebaseResult && window.__parlanceFirebaseResult("
                + quote(requestId) + ", null, " + quote("Cloud analysis is not available.") + ")");
    }

    private void finishPurchase(String callback, String requestId, String transactionId, String error) {
        if (error != null) {
            evaluateJs(callback + " && " + callback + "(" + quote(requestId) + ", null, "
                    + quote(error) + ")");
            return;
        }
        String payload = "{success:true,transactionId:" + quote(transactionId == null ? "" : transactionId) + "}";
        evaluateJs(callback + " && " + callback + "(" + quote(requestId) + ", " + payload + ", null)");
    }

    // MARK: - Callbacks into JavaScript

    /**
     * Publishes the new session before resolving the caller's promise, so the
     * web UI that re-renders on resolution already sees the current user.
     */
    private void finishAuthAction(String requestId, String error) {
        refreshAuthState();
        String errorArg = error == null ? "null" : quote(error);
        evaluateJs("window.__parlanceAuthResult && window.__parlanceAuthResult("
                + quote(requestId) + ", " + errorArg + ")");
    }

    void publishBillingConfig() {
        String price = billing.plusMonthlyDisplayPrice();
        String packPrice = billing.feedbackPackDisplayPrice();
        StringBuilder js = new StringBuilder("window.__parlanceUpdateConfig && window.__parlanceUpdateConfig({");
        js.append("isPlusActive:").append(billing.isPlusActive()).append(',');
        js.append("plusPurchaseAvailable:").append(billing.isPlusPurchasable()).append(',');
        js.append("feedbackPackPurchaseAvailable:").append(billing.isFeedbackPackPurchasable());
        if (price != null) {
            js.append(",plusMonthlyPriceDisplay:").append(quote(price));
        }
        if (packPrice != null) {
            js.append(",feedbackPackPriceDisplay:").append(quote(packPrice));
        }
        js.append("})");
        evaluateJs(js.toString());
    }

    void publishCoachConfig() {
        JSONArray coachLangs = new JSONArray();
        for (String lang : slm.availableLanguages()) {
            coachLangs.put(lang);
        }
        evaluateJs("window.__parlanceUpdateConfig && window.__parlanceUpdateConfig({"
                + "coachOnly:true,"
                + "parlanceCoachAvailable:" + (coachLangs.length() > 0) + ","
                + "parlanceCoachInstalling:" + slm.isInstalling() + ","
                + "parlanceCoachLanguages:" + coachLangs
                + "})");
    }

    /** Mirrors {@code AuthManager.injectAuth} so the web UI re-reads the session. */
    public void refreshAuthState() {
        evaluateJs("window.__PARLANCE_AUTH__ = " + auth.authStateJson() + ";"
                + "window.__parlanceAuthChanged && window.__parlanceAuthChanged();");
    }

    private void evaluateJs(String script) {
        webView.post(() -> webView.evaluateJavascript(script, null));
    }

    private static String quote(String value) {
        return JSONObject.quote(value == null ? "" : value);
    }

    private static String describe(Exception error) {
        String message = error.getLocalizedMessage();
        return message == null || message.isEmpty() ? error.toString() : message;
    }
}
