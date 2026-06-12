package com.autoride.admin;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.os.Build;
import androidx.annotation.NonNull;
import androidx.core.app.NotificationCompat;
import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;

@SuppressWarnings("SpellCheckingInspection")
public class AutorideAdminMessagingService extends FirebaseMessagingService {

    public static final String CHANNEL_ID   = "autoride_admin_high_priority";
    private static final String CHANNEL_NAME = "Autoride Admin Notifications";

    /**
     * Create (or update) the notification channel. Safe to call multiple times.
     * Must be called before any notification is posted.
     */
    public static void createNotificationChannel(Context ctx) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationManager mgr =
                (NotificationManager) ctx.getSystemService(Context.NOTIFICATION_SERVICE);
            if (mgr == null) return;

            // Delete old low-priority channel if it exists
            mgr.deleteNotificationChannel("autoride_admin_notifications");

            NotificationChannel ch = new NotificationChannel(
                CHANNEL_ID, CHANNEL_NAME, NotificationManager.IMPORTANCE_HIGH);
            ch.setDescription("Autoride admin operational alerts");
            ch.enableVibration(true);
            ch.setVibrationPattern(new long[]{0, 250, 250, 250});
            ch.enableLights(true);
            ch.setLightColor(Color.GREEN);
            ch.setShowBadge(true);
            ch.setLockscreenVisibility(android.app.Notification.VISIBILITY_PUBLIC);
            mgr.createNotificationChannel(ch);
        }
    }

    @Override
    public void onNewToken(@NonNull String token) {
        super.onNewToken(token);
        getSharedPreferences("autoride_admin_prefs", Context.MODE_PRIVATE)
            .edit()
            .putString("fcm_token", token)
            .apply();
    }

    @Override
    public void onMessageReceived(@NonNull RemoteMessage message) {
        super.onMessageReceived(message);

        String title = "Autoride Admin";
        String body  = "";

        // Prefer data payload (sent when app is foreground OR when we send data-only)
        if (message.getData().containsKey("title"))
            title = message.getData().get("title");
        if (message.getData().containsKey("body"))
            body = message.getData().get("body");

        // Fall back to notification payload
        if (message.getNotification() != null) {
            RemoteMessage.Notification n = message.getNotification();
            if ((title.equals("Autoride Admin")) && n.getTitle() != null) title = n.getTitle();
            if (body.isEmpty() && n.getBody() != null) body = n.getBody();
        }

        showNotification(title, body);
    }

    private void showNotification(String title, String body) {
        createNotificationChannel(this);

        NotificationManager mgr =
            (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);

        Intent intent = new Intent(this, MainActivity.class)
            .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        int piFlags = PendingIntent.FLAG_UPDATE_CURRENT |
            (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M ? PendingIntent.FLAG_IMMUTABLE : 0);
        PendingIntent pi = PendingIntent.getActivity(this, (int) System.currentTimeMillis(), intent, piFlags);

        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_stat_name)
            .setContentTitle(title)
            .setContentText(body)
            .setStyle(new NotificationCompat.BigTextStyle().bigText(body))
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_MAX)   // MAX forces heads-up popup
            .setDefaults(NotificationCompat.DEFAULT_ALL)    // sound + vibrate + lights
            .setVibrate(new long[]{0, 250, 250, 250})
            .setLights(Color.GREEN, 1000, 1000)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setCategory(NotificationCompat.CATEGORY_MESSAGE)
            .setContentIntent(pi);

        if (mgr != null) {
            mgr.notify((int) System.currentTimeMillis(), builder.build());
        }
    }
}
