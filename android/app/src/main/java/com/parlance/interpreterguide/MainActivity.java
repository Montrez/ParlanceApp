package com.parlance.interpreterguide;

import android.webkit.WebView;

import com.getcapacitor.BridgeActivity;
import com.getcapacitor.WebViewListener;
import com.getcapacitor.android.R;

public class MainActivity extends BridgeActivity {

    private ParlanceBridge parlanceBridge;

    @Override
    protected void load() {
        // Capacitor's Bridge constructor kicks off the first loadUrl, so both the
        // JavaScript interface and the page-load listener have to be attached
        // before super.load() runs. Registering afterwards would leave
        // window.ParlanceNative missing on the page the user actually sees.
        WebView webView = findViewById(R.id.webview);
        if (webView != null) {
            parlanceBridge = new ParlanceBridge(this, webView);
            webView.addJavascriptInterface(parlanceBridge, ParlanceBridge.JS_NAME);
        }

        bridgeBuilder.addWebViewListener(new WebViewListener() {
            @Override
            public void onPageLoaded(WebView view) {
                if (parlanceBridge != null) {
                    parlanceBridge.refreshAuthState();
                    parlanceBridge.publishCoachConfig();
                    parlanceBridge.publishBillingConfig();
                }
            }
        });

        super.load();
    }
}
