# Customer Mobile APK Build Instructions

## Latest Updates Included:
? **Pickup time fix** - Now defaults to current time instead of 6:00 AM
? **License image display** - Improved error handling and fallback support
? **License upload fixes** - Multiple fallback methods for Supabase issues

---

## Option 1: Build via Command Line (Fastest)

### Step 1: Open PowerShell or CMD
Navigate to the customer_mobile folder:
```bash
cd c:\Dev\AutorideSystem2sides\AutorideSystem\customer_mobile
```

### Step 2: Run the build script
```bash
BUILD_APK.bat
```

The APK will be created at:
```
android\app\build\outputs\apk\debug\app-debug.apk
```

---

## Option 2: Build via Android Studio (Recommended)

### Step 1: Open Android Studio

### Step 2: Open the project
- Click "Open" 
- Navigate to: `c:\Dev\AutorideSystem2sides\AutorideSystem\customer_mobile\android`
- Select the `android` folder

### Step 3: Wait for Gradle sync
- Android Studio will automatically sync the project
- Wait for "Sync successful" message

### Step 4: Build APK
- Click **Build** ? **Build Bundle(s) / APK(s)** ? **Build APK(s)**
- Wait for build to complete (usually 2-5 minutes)
- Click "locate" when the notification appears

### Step 5: Find the APK
Location: `android\app\build\outputs\apk\debug\app-debug.apk`

---

## Option 3: Quick Build Command

Open PowerShell in the android folder and run:
```powershell
cd c:\Dev\AutorideSystem2sides\AutorideSystem\customer_mobile\android
.\gradlew.bat assembleDebug
```

---

## Install on Device

### Via USB:
```bash
adb install android\app\build\outputs\apk\debug\app-debug.apk
```

### Via File Transfer:
1. Copy `app-debug.apk` to your phone
2. Open the file on your phone
3. Allow installation from unknown sources if prompted
4. Install the app

---

## Troubleshooting

### If Gradle build fails:
1. Clean the build:
   ```bash
   cd android
   .\gradlew.bat clean
   ```

2. Rebuild:
   ```bash
   .\gradlew.bat assembleDebug
   ```

### If Android Studio shows errors:
1. **File** ? **Invalidate Caches / Restart**
2. Wait for re-indexing
3. Try building again

### If you get signing errors:
The debug APK doesn't need signing - it uses the default debug keystore.

---

## Verify the Build

After building, check:
- ? APK file exists at specified location
- ? File size is reasonable (usually 10-50 MB)
- ? File name is `app-debug.apk`

---

## Testing Checklist

After installing on device, test:
1. ? Pickup time shows current time (not 6:00 AM)
2. ? License images display or show proper error messages
3. ? License upload works without 500 errors
4. ? Profile page loads correctly
5. ? Booking flow works end-to-end

---

## Need Help?

If you encounter issues:
1. Check the Gradle console output for error messages
2. Ensure Android SDK is properly installed
3. Make sure Java JDK is configured
4. Try cleaning and rebuilding
