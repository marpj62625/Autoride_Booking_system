# fix_customer_mobile_production.ps1
# Fixes customer mobile for production release:
# 1. Fix formatPHP to use peso sign (₱) instead of "PHP "
# 2. Remove all console.log debug statements from app.js and utils.js
# 3. Copy fixed files to android assets folder

$appJsPath = "customer_mobile\www\js\app.js"
$utilsJsPath = "customer_mobile\www\js\utils.js"
$androidAppJsPath = "customer_mobile\android\app\src\main\assets\public\js\app.js"
$androidUtilsJsPath = "customer_mobile\android\app\src\main\assets\public\js\utils.js"

Write-Host "=== Fixing Customer Mobile for Production ===" -ForegroundColor Cyan

# ── Fix utils.js ──────────────────────────────────────────────
Write-Host "`n[1/3] Fixing utils.js..." -ForegroundColor Yellow

$utilsContent = Get-Content $utilsJsPath -Raw -Encoding UTF8

# Fix formatPHP to use ₱ peso sign instead of "PHP "
$utilsContentFixed = $utilsContent -replace "return 'PHP ' \+ num\.toLocaleString", "return '₱' + num.toLocaleString"

# Remove the single console.log in compressImage (non-essential debug log)
$utilsContentFixed = $utilsContentFixed -replace "(?m)^\s*console\.log\('Compressed image from.*?\n", ""

$beforeCount = ([regex]::Matches($utilsContent, "console\.log")).Count
$afterCount  = ([regex]::Matches($utilsContentFixed, "console\.log")).Count
Write-Host "  utils.js: removed $($beforeCount - $afterCount) console.log(s)" -ForegroundColor Green

# Write fixed content
[System.IO.File]::WriteAllText((Resolve-Path $utilsJsPath), $utilsContentFixed, [System.Text.Encoding]::UTF8)

# ── Fix app.js ────────────────────────────────────────────────
Write-Host "`n[2/3] Fixing app.js..." -ForegroundColor Yellow

$appContent = Get-Content $appJsPath -Raw -Encoding UTF8

# Count before
$beforeCount = ([regex]::Matches($appContent, "console\.log")).Count

# Remove standalone console.log lines (lines that are ONLY a console.log statement)
# Pattern: optional whitespace + console.log(...) + semicolon + optional whitespace newline
$appFixed = $appContent -replace "(?m)^[^\S\r\n]*console\.log\([^)]*(?:\([^)]*\)[^)]*)*\);[^\S\r\n]*\r?\n", ""

# Handle multi-line console.log (with template strings or concatenation) - simpler single-line version
# Also handle console.log inside onclick attributes - replace with empty string
$appFixed = $appFixed -replace "console\.log\('[^']*'\);", ""
$appFixed = $appFixed -replace 'console\.log\("[^"]*"\);', ""

# Count after
$afterCount = ([regex]::Matches($appFixed, "console\.log")).Count
Write-Host "  app.js: removed $($beforeCount - $afterCount) console.log(s), $afterCount remaining" -ForegroundColor Green

# Write fixed app.js
[System.IO.File]::WriteAllText((Resolve-Path $appJsPath), $appFixed, [System.Text.Encoding]::UTF8)

# ── Copy to Android assets ────────────────────────────────────
Write-Host "`n[3/3] Copying fixed files to Android assets..." -ForegroundColor Yellow

if (Test-Path $androidAppJsPath) {
    Copy-Item $appJsPath $androidAppJsPath -Force
    Write-Host "  Copied app.js to android assets" -ForegroundColor Green
} else {
    Write-Host "  Android app.js path not found, skipping: $androidAppJsPath" -ForegroundColor DarkYellow
}

if (Test-Path $androidUtilsJsPath) {
    Copy-Item $utilsJsPath $androidUtilsJsPath -Force
    Write-Host "  Copied utils.js to android assets" -ForegroundColor Green
} else {
    Write-Host "  Android utils.js path not found, skipping: $androidUtilsJsPath" -ForegroundColor DarkYellow
}

Write-Host "`n=== Done! ===" -ForegroundColor Cyan
Write-Host "Verify: formatPHP now returns ₱ sign, console.logs removed." -ForegroundColor White
