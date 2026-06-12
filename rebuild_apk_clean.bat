@echo off
echo ===================================
echo CLEAN REBUILD CUSTOMER MOBILE APK
echo ===================================
echo.

cd /d "%~dp0customer_mobile"

echo [1/5] Cleaning Android build...
rmdir /s /q "android\.gradle" 2>nul
rmdir /s /q "android\app\build" 2>nul
rmdir /s /q "android\build" 2>nul

echo [2/5] Syncing Capacitor assets...
call npx cap sync android

echo [3/5] Copying latest app.js to assets...
copy /y "www\js\app.js" "android\app\src\main\assets\public\js\app.js"

echo [4/5] Opening Android Studio project...
start "" "android"

echo.
echo ===================================
echo MANUAL STEPS IN ANDROID STUDIO:
echo 1. File ? Invalidate Caches ? Invalidate and Restart
echo 2. Build ? Clean Project
echo 3. Build ? Rebuild Project
echo 4. Build ? Generate Signed Bundle/APK
echo ===================================
pause
