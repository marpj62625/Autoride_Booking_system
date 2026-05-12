package com.autoride.admin;

import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import com.getcapacitor.BridgeActivity;
import com.google.firebase.messaging.FirebaseMessaging;

public class MainActivity extends BridgeActivity {

    private static final int NOTIF_PERMISSION_CODE = 1001;
    private final Handler handler = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Request notification permission on Android 13+
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, android.Manifest.permission.POST_NOTIFICATIONS)
                    != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(
                    this,
                    new String[]{android.Manifest.permission.POST_NOTIFICATIONS},
                    NOTIF_PERMISSION_CODE
                );
            }
        }

        // Get FCM token and pass it to JS
        FirebaseMessaging.getInstance().getToken().addOnCompleteListener(task -> {
            if (task.isSuccessful() && task.getResult() != null) {
                String token = task.getResult();
                getSharedPreferences("autoride_admin_prefs", Context.MODE_PRIVATE)
                    .edit().putString("fcm_token", token).apply();
                String js = "window._adminFcmToken = '" + token + "'; " +
                            "if (typeof saveAdminFcmToken === 'function') saveAdminFcmToken('" + token + "');";
                getBridge().getWebView().post(() ->
                    getBridge().getWebView().evaluateJavascript(js, null)
                );
            }
        });
    }

    @Override
    public void onBackPressed() {
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
