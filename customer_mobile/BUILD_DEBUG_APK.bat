@echo off
echo ========================================
echo Building Autoride Customer Debug APK
echo ========================================
echo.
echo Updates included in this build:
echo - Loyalty points 50%% redemption limit
echo - Palette emoji icon for color selector
echo.

REM Navigate to android directory
cd android

echo [1/3] Cleaning previous builds...
call gradlew.bat clean
if errorlevel 1 (
    echo ERROR: Clean failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Building debug APK...
call gradlew.bat assembleDebug
if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Copying APK to root directory...
copy "app\build\outputs\apk\debug\app-debug.apk" "..\autoride-customer-debug-latest.apk"
if errorlevel 1 (
    echo ERROR: Failed to copy APK!
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD SUCCESSFUL!
echo ========================================
echo.
echo APK Location: customer_mobile\autoride-customer-debug-latest.apk
echo.
echo You can install this APK on your device.
echo.
pause
