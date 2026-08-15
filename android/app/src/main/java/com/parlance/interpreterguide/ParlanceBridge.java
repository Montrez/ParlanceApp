package com.parlance.interpreterguide;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.util.Log;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;

import com.google.firebase.functions.FirebaseFunctions;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.HashMap;
import java.util.Map;

/**
 * JavaScript bridge for the Parlance web layer, mirroring the iOS
 * WKScriptMessageHandler in {@code Parlance/ContentView.swift}.
 *
 * <p>Message shapes and the {@code window.__parlance*} callbacks are identical
 * on both platforms, so {@code journal.js} never branches on platform. Where the
 * two genuinely differ — Android has no Play Billing integration and no native
 * settings sheet — it is reported through the capability flags in
 * {@link #getConfig()} rather than through platform sniffing.
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

    public ParlanceBridge(Activity activity, WebView webView) {
        this.activity = activity;
        this.webView = webView;
        this.auth = new ParlanceAuth(activity);
        this.slm = new ParlanceSLMEngine(activity);
        this.slm.setAvailabilityListener(this::publishCoachConfig);
    }

    // MARK: - Synchronous state for hydration

    @JavascriptInterface
    public String getConfig() {
        JSONObject capabilities = new JSONObject();
        JSONObject config = new JSONObject();
        try {
            capabilities.put("nativeAuth", true);
            // Plus and call packs are StoreKit today. Until Play Billing is
            // wired up, advertising these would show buttons that cannot
            // complete, and would lock the medical/legal guides with no way to
            // unlock them.
            capabilities.put("inAppPurchase", false);
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
            config.put("isPlusActive", false);
            config.put("plusPurchaseAvailable", false);
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
                failPurchase("window.__parlancePurchaseResult", requestId);
                break;
            case "purchasePlus":
                failPurchase("window.__parlancePlusPurchaseResult", requestId);
                break;
            case "restorePlus":
                failPurchase("window.__parlancePlusRestoreResult", requestId);
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

    /**
     * Routes cloud analysis through the callable so it carries the natively
     * signed-in user. The web SDK has no session on Android — sign-in happens
     * in Java — so calling it from JavaScript would be unauthenticated.
     */
    private void analyzeFirebase(String requestId, JSONObject body) {
        Map<String, Object> data = new HashMap<>();
        data.put("sentence", body.optString("sentence", ""));
        data.put("language", body.optString("language", "es"));
        data.put("ragContext", body.optString("ragContext", ""));
        data.put("provider", body.optString("provider", ""));
        data.put("model", body.optString("model", ""));

        FirebaseFunctions.getInstance()
                .getHttpsCallable("analyzeText")
                .call(data)
                .addOnSuccessListener(result -> {
                    Object payload = result.getData();
                    Object wrapped = JSONObject.wrap(payload);
                    String json = wrapped == null ? "{}" : wrapped.toString();
                    evaluateJs("window.__parlanceFirebaseResult && window.__parlanceFirebaseResult("
                            + quote(requestId) + ", " + json + ", null)");
                })
                .addOnFailureListener(error -> evaluateJs(
                        "window.__parlanceFirebaseResult && window.__parlanceFirebaseResult("
                                + quote(requestId) + ", null, " + quote(describe(error)) + ")"));
    }

    private void failPurchase(String callback, String requestId) {
        evaluateJs(callback + " && " + callback + "(" + quote(requestId) + ", null, "
                + quote("Purchases are not available in the Android app yet.") + ")");
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
