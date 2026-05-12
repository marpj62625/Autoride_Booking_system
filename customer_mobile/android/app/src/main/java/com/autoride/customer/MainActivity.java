package com.autoride.customer;

import android.app.AlertDialog;
import android.os.Handler;
import android.os.Looper;
import android.widget.Toast;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {

    private boolean backPressedOnce = false;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable resetBackFlag = () -> backPressedOnce = false;

    @Override
    public void onBackPressed() {
        getBridge().getWebView().post(() ->
            getBridge().getWebView().evaluateJavascript(
                "(function() {" +
                "  try {" +
                // Check for open rental agreement modal
                "    var rentalModal = document.getElementById('rentalAgreementModal');" +
                "    if (rentalModal && rentalModal.parentNode) {" +
                "      rentalModal.remove();" +
                "      return 'closed_modal';" +
                "    }" +
                // Check for active overlays
                "    var overlays = document.querySelectorAll('.overlay-page.active');" +
                "    if (overlays.length > 0) {" +
                "      var last = overlays[overlays.length - 1];" +
                "      last.classList.remove('active');" +
                "      last.style.display = 'none';" +
                "      return 'closed_overlay';" +
                "    }" +
                // Check for active auth pages
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
                                // Navigation handled — nothing more to do
                                break;
                            case "on_login":
                            case "on_main":
                            default:
                                // Show native confirmation dialog
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
                // Clear session in JS then exit
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
