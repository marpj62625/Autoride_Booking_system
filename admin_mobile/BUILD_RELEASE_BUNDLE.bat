@echo off
echo ========================================
echo Building Autoride Admin Mobile Release AAB
echo (For Google Play Store Upload)
echo ========================================
echo.

cd android

echo Cleaning previous builds...
call gradlew.bat clean

echo.
echo Building Release App Bundle (AAB)...
call gradlew.bat bundleRelease

echo.
echo ========================================
if exist "app\build\outputs\bundle\release\app-release.aab" (
    echo [OK] BUILD SUCCESSFUL!
    echo.
    echo Release Bundle Location:
    echo android\app\build\outputs\bundle\release\app-release.aab
    echo.
    echo Note: You will need to sign this bundle using your Play Store release key before uploading.
    echo.
) else (
    echo [ERROR] BUILD FAILED!
    echo Please review the build errors above.
)
echo ========================================

pause
