# Google Sign-In Setup Guide

## What I Fixed

### 1. Backend API Endpoint (`/auth/google`)
- ? Now accepts both `credential` and `id_token` parameters
- ? Returns proper `user` object with correct field names (`fullName`, `isDriver`, `isVerified`)
- ? Handles both existing users and new user registration
- ? Auto-verifies users if Google email is verified

### 2. Frontend Implementation
- ? Added comprehensive logging to track the sign-in flow
- ? Better error handling and user feedback
- ? Proper extraction of user data from Google response
- ? Handles different response formats from Google Auth plugin

### 3. Configuration
- ? `capacitor.config.json` has correct `serverClientId`
- ? `config.py` has correct `GOOGLE_CLIENT_ID`
- ? Package name: `com.autoride.customer`
- ? SHA-1 fingerprint: `19:81:20:F2:38:BD:83:EA:9E:61:7E:D3:4A:29:4A:CF:11:6A:17:77`

## Google Cloud Console Checklist

Before testing, verify these settings in your Google Cloud Console:

### 1. OAuth Consent Screen
- Go to: https://console.cloud.google.com/apis/credentials/consent
- **User Type**: External (or Internal if G Suite)
- **App name**: Autoride
- **User support email**: Your email
- **Scopes**: `email`, `profile`, `openid`
- **Test users**: Add your test Gmail accounts (if in Testing mode)
- **Publishing status**: Testing or Published

### 2. Credentials
- Go to: https://console.cloud.google.com/apis/credentials
- You should have **3 OAuth clients**:

#### a) Android OAuth Client
- **Application type**: Android
- **Package name**: `com.autoride.customer`
- **SHA-1**: `19:81:20:F2:38:BD:83:EA:9E:61:7E:D3:4A:29:4A:CF:11:6A:17:77`

#### b) Web OAuth Client (IMPORTANT!)
- **Application type**: Web application
- **Name**: Autoride Web Client
- **Authorized JavaScript origins**: (can be empty)
- **Authorized redirect URIs**: (can be empty)
- **Copy the Client ID**: This should be `857792394948-vrf515cmh0d1lalr6g1d4g0alaqci903.apps.googleusercontent.com`

#### c) iOS OAuth Client (optional, for future iOS support)
- **Application type**: iOS
- **Bundle ID**: `com.autoride.customer`

### 3. Enable Required APIs
- Go to: https://console.cloud.google.com/apis/library
- Search and enable:
  - ? **Google+ API** (or People API)
  - ? **Google Identity Toolkit API**

## Testing Steps

### Step 1: Rebuild the App
```bash
cd customer_mobile
npx cap sync android
npx cap open android
```

### Step 2: Build and Run in Android Studio
1. Wait for Gradle sync to complete
2. Click **Run** (green play button)
3. Select your device/emulator

### Step 3: Test Google Sign-In
1. Open the app
2. Click **Sign in with Google** button
3. Select your Google account
4. Grant permissions

### Step 4: Check Logs
Open **Logcat** in Android Studio and filter by:
- `doGoogleLogin` - to see frontend logs
- `GoogleAuth` - to see plugin logs
- `chromium` - to see web view logs

## Common Error Codes and Solutions

### Error 12501: User Cancelled or Configuration Issue
**Causes:**
- SHA-1 fingerprint mismatch
- Wrong package name
- OAuth consent screen not configured
- App not added to test users (if in Testing mode)

**Solution:**
1. Verify SHA-1 in Google Console matches: `19:81:20:F2:38:BD:83:EA:9E:61:7E:D3:4A:29:4A:CF:11:6A:17:77`
2. Verify package name is: `com.autoride.customer`
3. Add your Gmail to test users in OAuth consent screen

### Error 10: Developer Error
**Causes:**
- Wrong `serverClientId` in capacitor.config.json
- Web OAuth client doesn't exist

**Solution:**
1. Verify Web OAuth Client exists in Google Console
2. Copy the Web Client ID (not Android Client ID!)
3. Update `capacitor.config.json` if needed
4. Run `npx cap sync android`

### Error 7: Network Error
**Causes:**
- No internet connection
- Google services blocked

**Solution:**
- Check internet connection
- Try on a different network

### "Something went wrong" (Generic Error)
**Causes:**
- APIs not enabled
- OAuth consent screen incomplete

**Solution:**
1. Enable Google+ API or People API
2. Complete OAuth consent screen setup
3. Publish the app or add test users

## Debugging Commands

### Check if plugin is installed:
```bash
cd customer_mobile
npm list @codetrix-studio/capacitor-google-auth
```

### Re-sync Capacitor:
```bash
npx cap sync android
```

### Check Android build.gradle:
```bash
cat android/app/build.gradle | grep -A 5 "dependencies"
```

### View current SHA-1:
```bash
cd android
./gradlew signingReport
```

## Expected Flow

1. User clicks "Sign in with Google"
2. Console log: `[doGoogleLogin] Starting Google Sign-In...`
3. Google account picker appears
4. User selects account and grants permissions
5. Console log: `[doGoogleLogin] Google Sign-In success: {...}`
6. Console log: `[doGoogleLogin] Extracted - email: xxx, name: xxx, hasToken: true`
7. Backend verifies token and creates/logs in user
8. Console log: `[doGoogleLogin] Backend response: {...}`
9. User is redirected to home page
10. Toast message: "Welcome, [Name]!"

## Files Modified

1. `backend/app.py` - Lines 1598-1770 (Google auth endpoint)
2. `customer_mobile/www/js/app.js` - Lines 665-720 (doGoogleLogin function)
3. `customer_mobile/capacitor.config.json` - GoogleAuth plugin config
4. `backend/config.py` - GOOGLE_CLIENT_ID

## Next Steps After Testing

If it works:
- ? Test with multiple Google accounts
- ? Test sign-out and sign-in again
- ? Verify user data is saved correctly in database

If it doesn't work:
1. Share the Logcat output (filter by `doGoogleLogin`)
2. Share any error messages from the app
3. Verify all checklist items above
4. Check if you can access Google Console and see the OAuth clients

## Support

If you encounter issues:
1. Check Logcat for error codes
2. Verify Google Console configuration
3. Try with a different Google account
4. Clear app data and try again
