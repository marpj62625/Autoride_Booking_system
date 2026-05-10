package com.autoride.admin;

import android.os.Handler;
import android.os.Looper;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {

    @Override
    public void onBackPressed() {
        // Dispatch a custom JS event so the web layer handles navigation.
        // The web layer calls App.exitApp() only when it wants to exit.
        getBridge().getWebView().post(() ->
            getBridge().getWebView().evaluateJavascript(
                "(function(){ " +
                "  var e = new Event('backbutton', {bubbles:true,cancelable:true}); " +
                "  document.dispatchEvent(e); " +
                "})()",
                null
            )
        );
    }
}
