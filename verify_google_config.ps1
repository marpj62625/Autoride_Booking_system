# Google Sign-In Configuration Verification Script
# Run this in PowerShell to check your current configuration

Write-Host "??????????????????????????????????????????????????????????????????" -ForegroundColor Cyan
Write-Host "?     Google Sign-In Configuration Verification                  ?" -ForegroundColor Cyan
Write-Host "??????????????????????????????????????????????????????????????????" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "customer_mobile")) {
    Write-Host "? Error: customer_mobile folder not found!" -ForegroundColor Red
    Write-Host "   Please run this script from the AutorideSystem folder" -ForegroundColor Yellow
    exit 1
}

Write-Host "1. Checking capacitor.config.json..." -ForegroundColor Yellow
Write-Host "?????????????????????????????????????????????????????????????????" -ForegroundColor Gray

$configPath = "customer_mobile\capacitor.config.json"
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
    $serverClientId = $config.plugins.GoogleAuth.serverClientId
    
    Write-Host "? Config file found" -ForegroundColor Green
    Write-Host "   Package ID: $($config.appId)" -ForegroundColor White
    Write-Host "   Server Client ID: $serverClientId" -ForegroundColor White
    
    # Check if it looks like a valid client ID
    if ($serverClientId -match "^\d+-[a-z0-9]+\.apps\.googleusercontent\.com$") {
        Write-Host "? Client ID format looks correct" -ForegroundColor Green
    } else {
        Write-Host "??  Client ID format looks unusual" -ForegroundColor Yellow
    }
} else {
    Write-Host "? Config file not found!" -ForegroundColor Red
}

Write-Host ""
Write-Host "2. Checking Android assets config..." -ForegroundColor Yellow
Write-Host "?????????????????????????????????????????????????????????????????" -ForegroundColor Gray

$assetsConfigPath = "customer_mobile\android\app\src\main\assets\capacitor.config.json"
if (Test-Path $assetsConfigPath) {
    $assetsConfig = Get-Content $assetsConfigPath -Raw | ConvertFrom-Json
    $assetsServerClientId = $assetsConfig.plugins.GoogleAuth.serverClientId
    
    Write-Host "? Assets config found" -ForegroundColor Green
    Write-Host "   Server Client ID: $assetsServerClientId" -ForegroundColor White
    
    # Compare with root config
    if ($serverClientId -eq $assetsServerClientId) {
        Write-Host "? Configs match!" -ForegroundColor Green
    } else {
        Write-Host "? Configs DON'T match! Need to run 'npx cap sync android'" -ForegroundColor Red
    }
} else {
    Write-Host "??  Assets config not found (will be created on sync)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "3. Checking backend config..." -ForegroundColor Yellow
Write-Host "?????????????????????????????????????????????????????????????????" -ForegroundColor Gray

$backendConfigPath = "backend\config.py"
if (Test-Path $backendConfigPath) {
    $backendConfig = Get-Content $backendConfigPath -Raw
    if ($backendConfig -match "GOOGLE_CLIENT_ID\s*=\s*['\"]([^'\"]+)['\"]") {
        $backendClientId = $matches[1]
        Write-Host "? Backend config found" -ForegroundColor Green
        Write-Host "   Google Client ID: $backendClientId" -ForegroundColor White
        
        # Check if backend and frontend match
        if ($serverClientId -eq $backendClientId) {
            Write-Host "? Backend and frontend configs match!" -ForegroundColor Green
        } else {
            Write-Host "??  Backend and frontend configs are different" -ForegroundColor Yellow
            Write-Host "   This is OK if you have separate Web and Android clients" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "? Backend config not found!" -ForegroundColor Red
}

Write-Host ""
Write-Host "4. Checking package name..." -ForegroundColor Yellow
Write-Host "?????????????????????????????????????????????????????????????????" -ForegroundColor Gray

$buildGradlePath = "customer_mobile\android\app\build.gradle"
if (Test-Path $buildGradlePath) {
    $buildGradle = Get-Content $buildGradlePath -Raw
    if ($buildGradle -match "applicationId\s+['\"]([^'\"]+)['\"]") {
        $packageName = $matches[1]
        Write-Host "? Package name: $packageName" -ForegroundColor Green
        
        if ($packageName -eq "com.autoride.customer") {
            Write-Host "? Package name is correct!" -ForegroundColor Green
        } else {
            Write-Host "? Package name should be: com.autoride.customer" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "???????????????????????????????????????????????????????????????????" -ForegroundColor Cyan
Write-Host "SUMMARY & NEXT STEPS" -ForegroundColor Cyan
Write-Host "???????????????????????????????????????????????????????????????????" -ForegroundColor Cyan
Write-Host ""
Write-Host "Current Server Client ID:" -ForegroundColor Yellow
Write-Host "  $serverClientId" -ForegroundColor White
Write-Host ""
Write-Host "??  ERROR CODE 10 means this Client ID is wrong or doesn't exist" -ForegroundColor Yellow
Write-Host ""
Write-Host "TO FIX:" -ForegroundColor Green
Write-Host "1. Go to: https://console.cloud.google.com/apis/credentials" -ForegroundColor White
Write-Host "2. Look for 'OAuth 2.0 Client IDs' section" -ForegroundColor White
Write-Host "3. Find the 'Web application' type client (NOT Android!)" -ForegroundColor White
Write-Host "4. Copy its Client ID" -ForegroundColor White
Write-Host "5. Update capacitor.config.json with that Client ID" -ForegroundColor White
Write-Host "6. Run: npx cap sync android" -ForegroundColor White
Write-Host "7. Rebuild in Android Studio" -ForegroundColor White
Write-Host ""
Write-Host "If you don't see a 'Web application' client:" -ForegroundColor Yellow
Write-Host "  - Click '+ CREATE CREDENTIALS'" -ForegroundColor White
Write-Host "  - Choose 'OAuth client ID'" -ForegroundColor White
Write-Host "  - Select 'Web application'" -ForegroundColor White
Write-Host "  - Name it 'Autoride Web Client'" -ForegroundColor White
Write-Host "  - Leave redirect URIs empty" -ForegroundColor White
Write-Host "  - Click CREATE and copy the Client ID" -ForegroundColor White
Write-Host ""
Write-Host "???????????????????????????????????????????????????????????????????" -ForegroundColor Cyan
