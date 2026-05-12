package com.autoride.customer;

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
        // Ask JS what the current navigation state is, then act accordingly
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
                // Check for active auth pages (register/otp ? go to login)
                "    var authPages = document.querySelectorAll('.auth-page.active');" +
                "    if (authPages.length > 0) {" +
                "      var id = authPages[0].id;" +
                "      if (id === 'page-register' || id === 'page-otp-verify' || id === 'page-phone-login') {" +
                "        if (typeof showPage === 'function') showPage('page-login');" +
                "        return 'went_to_login';" +
                "      }" +
                "      return 'on_login';" +
                "    }" +
                // On main pages
                "    return 'on_main';" +
                "  } catch(e) { return 'error'; }" +
                "})()",
                result -> {
                    // result comes back as a JSON string with quotes, e.g. "\"on_main\""
                    String state = result != null ? result.replace("\"", "") : "on_main";
                    handler.post(() -> {
                        switch (state) {
                            case "closed_modal":
                            case "closed_overlay":
                            case "went_to_login":
                                // Navigation handled in JS — do nothing more
                                break;
                            case "on_login":
                            case "on_main":
                                // Double-back to logout and exit
                                if (backPressedOnce) {
                                    handler.removeCallbacks(resetBackFlag);
                                    // Clear session and exit
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
                                } else {
                                    backPressedOnce = true;
                                    Toast.makeText(this, "Press back again to logout and exit", Toast.LENGTH_SHORT).show();
                                    handler.postDelayed(resetBackFlag, 2000);
                                }
                                break;
                            default:
                                // Fallback — just show toast
                                if (backPressedOnce) {
                                    finishAffinity();
                                } else {
                                    backPressedOnce = true;
                                    Toast.makeText(this, "Press back again to exit", Toast.LENGTH_SHORT).show();
                                    handler.postDelayed(resetBackFlag, 2000);
                                }
                                break;
                        }
                    });
                }
            )
        );
    }
}
