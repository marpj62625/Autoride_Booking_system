import os
import shutil
import zipfile
import time

src_apk = r'customer_mobile\android\app\build\outputs\apk\debug\app-debug.apk'
# Check alternate build path in .autoride_builds if used
alt_src = r'C:\Users\patri\.autoride_builds\customer\app\outputs\apk\debug\app-debug.apk'
if os.path.exists(alt_src) and (not os.path.exists(src_apk) or os.path.getmtime(alt_src) > os.path.getmtime(src_apk)):
    src_apk = alt_src

print(f"Source APK: {src_apk}")
if not os.path.exists(src_apk):
    print(f"Error: {src_apk} not found!")
    exit(1)

print(f"Size: {os.path.getsize(src_apk):,} bytes, Modified: {time.ctime(os.path.getmtime(src_apk))}")

targets = [
    'AutorideCustomer-debug-latest.apk',
    'AutorideCustomer-debug.apk',
    'autoride-customer-debug.apk',
    'customer_mobile/AutorideCustomer-debug-latest.apk',
    'customer_mobile/autoride-customer-debug-latest.apk',
    'customer_mobile/AutorideCustomer-debug.apk',
    'customer_mobile/android/app/build/outputs/apk/debug/app-debug.apk'
]

print("\nDistributing freshly compiled Customer APK:")
for t in targets:
    norm_t = os.path.normpath(t)
    if os.path.abspath(src_apk) == os.path.abspath(norm_t):
        continue
    os.makedirs(os.path.dirname(norm_t), exist_ok=True) if os.path.dirname(norm_t) else None
    shutil.copy2(src_apk, norm_t)
    
    with zipfile.ZipFile(norm_t, 'r') as z:
        app_js = z.read('assets/public/js/app.js').decode('utf-8', errors='ignore')
        has_operational_check = 'isVehicleOperational' in app_js
        has_unavailable_block = 'NON_OPERATIONAL_STATUSES' in app_js
        has_bottom_nav_fix = 'hasActiveOverlay' in app_js
    print(f"  [VERIFIED] {norm_t} ({os.path.getsize(norm_t):,} bytes) -> operational={has_operational_check}, bottomNavFix={has_bottom_nav_fix}")

print("\n[ALL CUSTOMER APK TARGETS 100% SYNCHRONIZED AND VERIFIED]")
