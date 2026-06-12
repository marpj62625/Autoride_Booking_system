# ?? ANDROID STUDIO BUILD GUIDE - AUTORIDE MOBILE APPS

## ?? **USE THESE PATHS IN ANDROID STUDIO**

**? CORRECT PROJECT LOCATION:**
```
C:\Dev\AutorideSystem2sides\AutorideSystem\
```

**? AVOID OneDrive LOCATION:**
```
C:\Users\patri\OneDrive\Desktop\AutorideSystem2sides\ ? DON'T USE THIS
```

## ?? **STEP-BY-STEP BUILD PROCESS**

### **1. Customer Mobile App**
```
Open Android Studio ? Open Project ? Navigate to:
C:\Dev\AutorideSystem2sides\AutorideSystem\customer_mobile\android\
```

### **2. Admin Mobile App**  
```
Open Android Studio ? Open Project ? Navigate to:
C:\Dev\AutorideSystem2sides\AutorideSystem\admin_mobile\android\
```

## ?? **BEFORE BUILDING - CLEAN EVERYTHING**

### **Option A: Android Studio Method**
1. **File** ? **Invalidate Caches & Restart**
2. **Build** ? **Clean Project**  
3. **Build** ? **Rebuild Project**
4. **Build** ? **Generate Signed Bundle / APK**

### **Option B: Command Line Method**
```bash
# For Customer Mobile
cd "C:\Dev\AutorideSystem2sides\AutorideSystem\customer_mobile\android"
./gradlew clean
./gradlew build

# For Admin Mobile  
cd "C:\Dev\AutorideSystem2sides\AutorideSystem\admin_mobile\android"
./gradlew clean
./gradlew build
```

## ?? **IF STILL GETTING FILE LOCK ERRORS**

### **Nuclear Option - Force Delete Locked Files**
Run these commands **as Administrator** in PowerShell:

```powershell
# Customer Mobile - Force Clean
cd "C:\Dev\AutorideSystem2sides\AutorideSystem\customer_mobile\android"
taskkill /f /im java.exe
taskkill /f /im gradle.exe  
Remove-Item -Recurse -Force "app\build" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ".gradle" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "node_modules\@codetrix-studio\capacitor-google-auth\android\build" -ErrorAction SilentlyContinue

# Admin Mobile - Force Clean
cd "C:\Dev\AutorideSystem2sides\AutorideSystem\admin_mobile\android"  
taskkill /f /im java.exe
taskkill /f /im gradle.exe
Remove-Item -Recurse -Force "app\build" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ".gradle" -ErrorAction SilentlyContinue
```

### **Alternative: Use Different Build Output**
In Android Studio:
1. **File** ? **Settings** ? **Build, Execution, Deployment** ? **Compiler**
2. Change **Build process heap size** to 2048 MB
3. Enable **Use in-process build** 
4. Enable **Configure on demand**

## ?? **WHAT'S BEEN FIXED IN THE COPIED PROJECT**

### **Customer Mobile (`C:\Dev\...\customer_mobile\`)**
- ? Push notification crash fixed in `www/js/app.js`
- ? Firebase configuration restored  
- ? Safe error handling for PushNotifications object

### **Admin Mobile (`C:\Dev\...\admin_mobile\`)**
- ? Push notification button fixed in `www/index.html`
- ? Enhanced testAdminPushNotification() function
- ? Better UI with gradient backgrounds and animations

## ?? **BUILD SUCCESS INDICATORS**

### **? Successful Build**
- No file locking errors
- APK generated in `app/build/outputs/apk/debug/`
- App installs and runs without crashing
- Push notifications work (no more crashes on startup)

### **? Build Failures to Watch For**
- `Unable to delete directory` errors
- `Failed to delete some children` messages  
- Java/Gradle process lock errors
- Google Auth plugin compilation errors

## ?? **AFTER SUCCESSFUL BUILD**

### **Test Checklist:**
1. **Install APK** on Android device
2. **Customer App**: Test login, booking, push notifications
3. **Admin App**: Test login, push notification button, dashboard
4. **License Details**: Verify no more 413 errors (after backend fix)

## ? **CURRENT STATUS**
- ? **Push notification fixes**: Deployed and committed
- ? **License details backend**: Fix deploying to Vercel now  
- ?? **APK builds**: Ready to test with cleaned project

**START WITH ANDROID STUDIO NOW!** ??