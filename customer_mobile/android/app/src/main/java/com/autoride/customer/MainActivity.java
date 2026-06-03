package com.autoride.customer;

import android.app.AlertDialog;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import androidx.activity.OnBackPressedCallback;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import com.getcapacitor.BridgeActivity;
import com.google.firebase.messaging.FirebaseMessaging;
import com.codetrixstudio.capacitor.GoogleAuth.GoogleAuth;

@SuppressWarnings("SpellCheckingInspection")
public class MainActivity extends BridgeActivity {

    private static final int NOTIF_PERMISSION_CODE = 1001;
    private final Handler handler = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Register GoogleAuth plugin
        registerPlugin(GoogleAuth.class);

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
            getSharedPreferences("autoride_prefs", Context.MODE_PRIVATE)
                .edit()
                .putString("fcm_token", token)
                .apply();
            String js = "window._fcmToken = '" + token + "';" +
                        "if(typeof saveFcmToken==='function') saveFcmToken('" + token + "');";
            getBridge().getWebView().post(
                () -> getBridge().getWebView().evaluateJavascript(js, null)
            );
        });
    }

    private void registerBackHandler() {
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                String js =
                    "(function(){" +
                    "  try{" +
                    "    var m=document.getElementById('rentalAgreementModal');" +
                    "    if(m&&m.parentNode){m.remove();return 'closed_modal';}" +
                    "    var o=document.querySelectorAll('.overlay-page.active');" +
                    "    if(o.length>0){var l=o[o.length-1];l.classList.remove('active');l.style.display='none';return 'closed_overlay';}" +
                    "    var a=document.querySelectorAll('.auth-page.active');" +
                    "    if(a.length>0){" +
                    "      var id=a[0].id;" +
                    "      if(id==='page-register'||id==='page-otp-verify'||id==='page-phone-login'){" +
                    "        if(typeof showPage==='function')showPage('page-login');return 'went_to_login';" +
                    "      }return 'on_login';" +
                    "    }return 'on_main';" +
                    "  }catch(e){return 'error';}" +
                    "})()";

                getBridge().getWebView().post(() ->
                    getBridge().getWebView().evaluateJavascript(js, result -> {
                        String state = result != null ? result.replace("\"", "") : "on_main";
                        handler.post(() -> {
                            switch (state) {
                                case "closed_modal":
                                case "closed_overlay":
                                case "went_to_login":
                                    break;
                                default:
                                    showExitDialog();
                                    break;
                            }
                        });
                    })
                );
            }
        });
    }

    private void showExitDialog() {
        new AlertDialog.Builder(this)
            .setTitle("Logout & Exit")
            .setMessage("Are you sure you want to logout and exit?")
            .setPositiveButton("Logout & Exit", (d, w) -> {
                String js =
                    "(function(){" +
                    "  try{" +
                    "    if(typeof unsubscribeFromNotifications==='function') unsubscribeFromNotifications();" +
                    "    if(typeof Session!=='undefined') Session.clear();" +
                    "  }catch(e){}" +
                    "})()";
                getBridge().getWebView().post(
                    () -> getBridge().getWebView().evaluateJavascript(js, null)
                );
                finishAffinity();
            })
            .setNegativeButton("Cancel", (d, w) -> d.dismiss())
            .setCancelable(true)
            .show();
    }
}
