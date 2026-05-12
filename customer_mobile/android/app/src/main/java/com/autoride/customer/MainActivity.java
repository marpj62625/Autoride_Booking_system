package com.autoride.customer;

import android.app.AlertDialog;
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
                getSharedPreferences("autoride_prefs", Context.MODE_PRIVATE)
                    .edit().putString("fcm_token", token).apply();
                String js = "window._fcmToken = '" + token + "'; " +
                            "if (typeof saveFcmToken === 'function') saveFcmToken('" + token + "');";
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
                "(function() {" +
                "  try {" +
                "    var rentalModal = document.getElementById('rentalAgreementModal');" +
                "    if (rentalModal && rentalModal.parentNode) {" +
                "      rentalModal.remove();" +
                "      return 'closed_modal';" +
                "    }" +
                "    var overlays = document.querySelectorAll('.overlay-page.active');" +
                "    if (overlays.length > 0) {" +
                "      var last = overlays[overlays.length - 1];" +
                "      last.classList.remove('active');" +
                "      last.style.display = 'none';" +
                "      return 'closed_overlay';" +
                "    }" +
                "    var authPages = document.querySelectorAll('.auth-page.active');" +
                "    if (authPages.length > 0) {" +
                "      var id = authPages[0].id;" +
                "      if (id === 'page-register' || id === 'page-otp-verify' || id === 'page-phone-login') {" +
                "        if (typeof showPage === 'function') showPage('page-login');" +
                "        return 'went_to_login';" +
                "      }" +
                "      return 'on_login';" +
                "    }" +
                "    return 'on_main';" +
                "  } catch(e) { return 'error'; }" +
                "})()",
                result -> {
                    String state = result != null ? result.replace("\"", "") : "on_main";
                    handler.post(() -> {
                        switch (state) {
                            case "closed_modal":
                            case "closed_overlay":
                            case "went_to_login":
                                break;
                            case "on_login":
                            case "on_main":
                            default:
                                showExitConfirmDialog();
                                break;
                        }
                    });
                }
            )
        );
    }

    private void showExitConfirmDialog() {
        new AlertDialog.Builder(this)
            .setTitle("Logout & Exit")
            .setMessage("Are you sure you want to logout and exit the app?")
            .setPositiveButton("Logout & Exit", (dialog, which) -> {
                getBridge().getWebView().post(() ->
                    getBridge().getWebView().evaluateJavascript(
                        "(function(){" +
                        "  try {" +
                        "    if (typeof unsubscribeFromNotifications === 'function') unsubscribeFromNotifications();" +
                        "    if (typeof Session !== 'undefined') Session.clear();" +
                        "  } catch(e) {}" +
                        "})()",
                        null
                    )
                );
                finishAffinity();
            })
            .setNegativeButton("Cancel", (dialog, which) -> dialog.dismiss())
            .setCancelable(true)
            .show();
    }
}
