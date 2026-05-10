package com.autoride.customer;

import android.os.Handler;
import android.os.Looper;
import android.widget.Toast;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {

    private boolean backPressedOnce = false;
    private final Handler handler = new Handler(Looper.getMainLooper());

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
