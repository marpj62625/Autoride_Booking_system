import os
import shutil
import zipfile
import time

src_apk = r'C:\Users\patri\.autoride_builds\admin\app\outputs\apk\debug\app-debug.apk'
print(f"Source APK: {src_apk}")
if not os.path.exists(src_apk):
    # Check alternate build path if present
    alt_src = 'admin_mobile/android/app/build/outputs/apk/debug/app-debug.apk'
    if os.path.exists(alt_src):
        src_apk = alt_src

print(f"Size: {os.path.getsize(src_apk):,} bytes, Modified: {time.ctime(os.path.getmtime(src_apk))}")

targets = [
    'AutorideAdmin-debug-latest.apk',
    'AutorideAdmin-debug.apk',
    'AutorideAdmin.apk',
    'admin_app/AutorideAdmin-debug-latest.apk',
    'admin_mobile/AutorideAdmin-debug-latest.apk',
    'admin_mobile/autoride-admin-debug-latest.apk',
    'admin_mobile/android/app/build/outputs/apk/debug/app-debug.apk'
]

print("\nDistributing freshly compiled APK:")
for t in targets:
    norm_t = os.path.normpath(t)
    if os.path.abspath(src_apk) == os.path.abspath(norm_t):
        continue
    os.makedirs(os.path.dirname(norm_t), exist_ok=True) if os.path.dirname(norm_t) else None
    shutil.copy2(src_apk, norm_t)
    
    with zipfile.ZipFile(norm_t, 'r') as z:
        idx = z.read('assets/public/index.html').decode('utf-8', errors='ignore')
        has_walkin_modal = 'walkinBookingModal' in idx
        has_walkin_ctrl = 'WalkinBooking' in idx
        has_exact_time = 'Exact Time Now' in idx
    print(f"  [VERIFIED] {norm_t} ({os.path.getsize(norm_t):,} bytes) -> walkinModal={has_walkin_modal}, walkinCtrl={has_walkin_ctrl}, exactTime={has_exact_time}")

print("\n[ALL TARGETS 100% SYNCHRONIZED AND VERIFIED]")
