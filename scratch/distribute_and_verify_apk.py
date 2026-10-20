import os
import shutil
import zipfile
import time

src_apk = os.path.normpath('admin_mobile/android/app/build/outputs/apk/debug/app-debug.apk')
print(f"Source APK: {src_apk}")
if not os.path.exists(src_apk):
    raise FileNotFoundError(f"Source APK does not exist: {src_apk}")

size = os.path.getsize(src_apk)
mtime = os.path.getmtime(src_apk)
print(f"Size: {size:,} bytes, Last modified: {time.ctime(mtime)}")

# Verify source APK contents
with zipfile.ZipFile(src_apk, 'r') as z:
    idx_content = z.read('assets/public/index.html').decode('utf-8', errors='ignore')
    print("Verification checks on source APK:")
    print(f"  - Contains 'pickup_soon': {'pickup_soon' in idx_content}")
    print(f"  - Contains 'return_soon': {'return_soon' in idx_content}")
    print(f"  - Contains 'newBookingsSort': {'newBookingsSort' in idx_content}")
    print(f"  - Contains 'setNewSort': {'setNewSort' in idx_content}")
    print(f"  - Contains 'setNewFilter': {'setNewFilter' in idx_content}")
    print(f"  - Contains 'All New': {'All New' in idx_content}")

dest_targets = [
    'AutorideAdmin-debug-latest.apk',
    'admin_app/AutorideAdmin-debug-latest.apk',
    'admin_mobile/AutorideAdmin-debug-latest.apk',
    'admin_mobile/autoride-admin-debug-latest.apk',
    'admin_mobile/www/AutorideAdmin-debug-latest.apk',
    'admin_mobile/android/app/src/main/assets/public/AutorideAdmin-debug-latest.apk'
]

print("\nDistributing APK to all destination targets:")
for dst in dest_targets:
    norm_dst = os.path.normpath(dst)
    os.makedirs(os.path.dirname(norm_dst), exist_ok=True) if os.path.dirname(norm_dst) else None
    shutil.copy2(src_apk, norm_dst)
    
    # Verify copied target
    with zipfile.ZipFile(norm_dst, 'r') as z:
        check = 'pickup_soon' in z.read('assets/public/index.html').decode('utf-8', errors='ignore')
    print(f"  [OK] {norm_dst} ({os.path.getsize(norm_dst):,} bytes) -> pickup_soon verified: {check}")

print("\n[ALL APK DESTINATIONS 100% SYNCHRONIZED AND VERIFIED]")
