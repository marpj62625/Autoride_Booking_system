package com.autoride.admin;

import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import androidx.activity.OnBackPressedCallback;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import com.getcapacitor.BridgeActivity;
import com.google.firebase.messaging.FirebaseMessaging;

@SuppressWarnings("SpellCheckingInspection")
public class MainActivity extends BridgeActivity {

    private static final int NOTIF_PERMISSION_CODE = 1001;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        AutorideAdminMessagingService.createNotificationChannel(this);
        requestNotificationPermission();
        fetchAndForwardFcmToken();
        registerBackHandler();
    }

    private void requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this,
                    android.Manifest.permission.POST_NOTIFICATIONS)
                    != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(this,
                    new String[]{android.Manifest.permission.POST_NOTIFICATIONS},
                    NOTIF_PERMISSION_CODE);
            }
        }
    }

    private void fetchAndForwardFcmToken() {
        FirebaseMessaging.getInstance().getToken().addOnCompleteListener(task -> {
            if (!task.isSuccessful() || task.getResult() == null) return;
            String token = task.getResult();
            getSharedPreferences("autoride_admin_prefs", Context.MODE_PRIVATE)
                .edit()
                .putString("fcm_token", token)
                .apply();
            String js = "window._adminFcmToken = '" + token + "';" +
                        "if(typeof saveAdminFcmToken==='function') saveAdminFcmToken('" + token + "');";
            getBridge().getWebView().post(
                () -> getBridge().getWebView().evaluateJavascript(js, null)
            );
        });
    }

    private void registerBackHandler() {
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                getBridge().getWebView().post(() ->
                    getBridge().getWebView().evaluateJavascript(
                        "(function(){" +
                        "  var e=new Event('backbutton',{bubbles:true,cancelable:true});" +
                        "  document.dispatchEvent(e);" +
                        "})()",
                        null
                    )
                );
            }
        });
    }
}
