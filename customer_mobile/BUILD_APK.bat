@echo off
echo ========================================
echo Building Autoride Customer Mobile APK
echo ========================================
echo.
echo Update: Pickup time fix + License image display improvements
echo.

cd android

echo Cleaning previous build...
call gradlew.bat clean

echo.
echo Building debug APK...
call gradlew.bat assembleDebug

echo.
echo ========================================
if exist "app\build\outputs\apk\debug\app-debug.apk" (
    echo ? BUILD SUCCESS!
    echo.
    echo APK Location: android\app\build\outputs\apk\debug\app-debug.apk
    echo.
    echo You can now:
    echo 1. Install on device: adb install app\build\outputs\apk\debug\app-debug.apk
    echo 2. Copy to phone and install manually
    echo.
) else (
    echo ? BUILD FAILED!
    echo Check the error messages above.
)
echo ========================================

pause
