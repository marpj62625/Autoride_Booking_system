package com.autoride.customer;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import androidx.annotation.NonNull;
import androidx.core.app.NotificationCompat;
import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;

@SuppressWarnings("SpellCheckingInspection")
public class AutorideMessagingService extends FirebaseMessagingService {

    private static final String CHANNEL_ID   = "autoride_notifications";
    private static final String CHANNEL_NAME = "Autoride Notifications";

    @Override
    public void onNewToken(@NonNull String token) {
        super.onNewToken(token);
        getSharedPreferences("autoride_prefs", Context.MODE_PRIVATE)
            .edit()
            .putString("fcm_token", token)
            .apply();
    }

    @Override
    public void onMessageReceived(@NonNull RemoteMessage message) {
        super.onMessageReceived(message);

        String title = "Autoride";
        String body  = "";

        if (message.getNotification() != null) {
            RemoteMessage.Notification n = message.getNotification();
            if (n.getTitle() != null) title = n.getTitle();
            if (n.getBody()  != null) body  = n.getBody();
        }
        if (body.isEmpty() && message.getData().containsKey("body"))
            body = message.getData().get("body");
        if (message.getData().containsKey("title"))
            title = message.getData().get("title");

        showNotification(title, body);
    }

    private void showNotification(String title, String body) {
        NotificationManager mgr =
            (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel ch = new NotificationChannel(
                CHANNEL_ID, CHANNEL_NAME, NotificationManager.IMPORTANCE_HIGH);
            ch.setDescription("Autoride booking and payment notifications");
            ch.enableVibration(true);
            mgr.createNotificationChannel(ch);
        }

        Intent intent = new Intent(this, MainActivity.class)
            .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
        int piFlags = PendingIntent.FLAG_ONE_SHOT |
            (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M ? PendingIntent.FLAG_IMMUTABLE : 0);
        PendingIntent pi = PendingIntent.getActivity(this, 0, intent, piFlags);

        mgr.notify((int) System.currentTimeMillis(),
            new NotificationCompat.Builder(this, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle(title)
                .setContentText(body)
                .setStyle(new NotificationCompat.BigTextStyle().bigText(body))
                .setAutoCancel(true)
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setContentIntent(pi)
                .build());
    }
}
