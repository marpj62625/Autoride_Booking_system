# Firebase Setup Guide for Autoride Push Notifications

## Quick Setup (5 minutes)

### Step 1: Create Firebase Project
1. Go to https://console.firebase.google.com
2. Click "Create a project"
3. Project name: "Autoride Push Notifications"
4. Disable Google Analytics (not needed)
5. Click "Create project"

### Step 2: Add Android App
1. In your new project, click "Add app" ? Android icon
2. Package name: `com.autoride.customer`
3. App nickname: "Autoride Customer"
4. Skip SHA-1 for now
5. Click "Register app"

### Step 3: Download Configuration
1. Download `google-services.json`
2. Replace the file at: `customer_mobile/android/app/google-services.json`

### Step 4: Get Server Key
1. Go to Project Settings (gear icon)
2. Click "Cloud Messaging" tab
3. Copy the "Server key" 
4. It looks like: `AAAABBCCDDee:APA91bF...` (long key)

### Step 5: Update Backend Config
1. Open `backend/config.py`
2. Replace the FCM_SERVER_KEY value:
```python
FCM_SERVER_KEY = os.getenv('FCM_SERVER_KEY', 'YOUR_REAL_SERVER_KEY_HERE')
```

### Step 6: Test the System
1. Rebuild the APK: `cd customer_mobile/android && ./gradlew assembleDebug`
2. Install on device and login
3. Test push notification: `python test_push_notifications.py <user_id>`

## Alternative: Use Environment Variable
Set the server key as environment variable:
```bash
export FCM_SERVER_KEY="YOUR_REAL_SERVER_KEY_HERE"
```

## Troubleshooting

### "Push failed: Unknown error"
- Check server key is correct
- Verify google-services.json is updated
- Rebuild APK after changes

### No FCM token generated
- Check app permissions
- Verify Firebase SDK is included
- Check Android logs: `adb logcat | grep FCM`

### Testing without Firebase
- In-app notifications will still work
- Only push notifications need Firebase
- System gracefully degrades

## Quick Test Commands

Test FCM configuration:
```bash
curl https://your-domain.com/api/test-fcm-config
```

Test push to user:
```bash
curl -X POST https://your-domain.com/api/test-push/123 \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "message": "Hello from Autoride!"}'
```

## Production Checklist
- [ ] Real Firebase project created
- [ ] Server key configured
- [ ] google-services.json updated
- [ ] APK rebuilt and tested
- [ ] Push notifications working on real device