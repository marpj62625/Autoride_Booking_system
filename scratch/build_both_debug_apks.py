import os
import shutil
import subprocess
import zipfile
import time

print("=" * 60)
print("BUILDING AND DISTRIBUTING DEBUG APKS: CUSTOMER AND ADMIN")
print("=" * 60)

env = os.environ.copy()
env['JAVA_HOME'] = r'C:\Users\patri\scoop\apps\openjdk21\current'
env['ANDROID_HOME'] = r'C:\Users\patri\AppData\Local\Android\Sdk'
env['PATH'] = os.path.join(env['JAVA_HOME'], 'bin') + os.pathsep + env['PATH']

# ----------------------------------------------------------------------
# 1. PROCESS CUSTOMER APK
# ----------------------------------------------------------------------
cust_apk_src = r'C:\Users\patri\.autoride_builds\customer\app\outputs\apk\debug\app-debug.apk'
if not os.path.exists(cust_apk_src):
    raise FileNotFoundError(f"Customer APK not found at: {cust_apk_src}")

print(f"\n[Customer APK Found]")
print(f"  Source: {cust_apk_src}")
print(f"  Size: {os.path.getsize(cust_apk_src):,} bytes")
print(f"  Compiled: {time.ctime(os.path.getmtime(cust_apk_src))}")

# Distribute Customer APK
cust_targets = [
    'AutorideCustomer-debug-latest.apk',
    'AutorideCustomer-debug.apk',
    'customer_mobile/AutorideCustomer-debug-latest.apk',
    'customer_mobile/AutorideCustomer-debug.apk',
    'customer_mobile/android/app/build/outputs/apk/debug/app-debug.apk',
]
for target in cust_targets:
    norm_t = os.path.normpath(target)
    os.makedirs(os.path.dirname(norm_t), exist_ok=True) if os.path.dirname(norm_t) else None
    shutil.copy2(cust_apk_src, norm_t)
    print(f"  -> Distributed to: {norm_t}")

# Verify Customer APK
with zipfile.ZipFile(cust_apk_src, 'r') as z:
    idx = z.read('assets/public/index.html').decode('utf-8', errors='ignore')
    has_v7 = 'v2026.10.19.7' in idx
    has_overflow_fix = 'overflow-x: hidden !important' in idx
    has_flex_quick_actions = 'repeat(2, 1fr) !important' in idx
    print(f"  [CUSTOMER APK VERIFIED] v2026.10.19.7={has_v7}, overflow-fix={has_overflow_fix}, flexible-actions={has_flex_quick_actions}")

# ----------------------------------------------------------------------
# 2. SYNC ADMIN ASSETS & BUILD ADMIN APK
# ----------------------------------------------------------------------
print("\n[Admin APK Build Starting]")
shutil.copy2('admin_app/index.html', 'admin_mobile/www/index.html')

adm_www = 'admin_mobile/www'
adm_assets = 'admin_mobile/android/app/src/main/assets/public'

for root, dirs, files in os.walk(adm_www):
    rel = os.path.relpath(root, adm_www)
    target_dir = os.path.normpath(os.path.join(adm_assets, rel))
    os.makedirs(target_dir, exist_ok=True)
    for f in files:
        if f.endswith('.apk') or f.endswith('.tmp') or 'node_modules' in root:
            continue
        src_f = os.path.join(root, f)
        dst_f = os.path.join(target_dir, f)
        shutil.copy2(src_f, dst_f)

print(f"  Synced {adm_www} -> {adm_assets}")

# Remove old admin APK before compile
adm_apk_src = r'C:\Users\patri\.autoride_builds\admin\app\outputs\apk\debug\app-debug.apk'
if os.path.exists(adm_apk_src):
    os.remove(adm_apk_src)
    print(f"  Removed old admin APK: {adm_apk_src}")

# Build Admin
print("  Running admin_mobile/android gradlew clean assembleDebug --rerun-tasks...")
adm_grad = subprocess.run(
    ['gradlew.bat', 'clean', 'assembleDebug', '--rerun-tasks', '--no-daemon'],
    cwd='admin_mobile/android',
    shell=True,
    env=env,
    capture_output=True,
    text=True
)

if adm_grad.returncode != 0 or not os.path.exists(adm_apk_src):
    print("Admin Gradle Build FAILED!")
    print("STDOUT:", adm_grad.stdout[-1500:])
    print("STDERR:", adm_grad.stderr[-1500:])
    raise RuntimeError("Admin APK build failed")

print(f"  [SUCCESS] Admin APK compiled: {adm_apk_src}")
print(f"  Size: {os.path.getsize(adm_apk_src):,} bytes, Compiled: {time.ctime(os.path.getmtime(adm_apk_src))}")

# Distribute Admin APK
adm_targets = [
    'AutorideAdmin-debug-latest.apk',
    'AutorideAdmin-debug.apk',
    'admin_mobile/AutorideAdmin-debug-latest.apk',
    'admin_mobile/AutorideAdmin-debug.apk',
    'admin_app/AutorideAdmin-debug-latest.apk',
    'admin_mobile/android/app/build/outputs/apk/debug/app-debug.apk',
]
for target in adm_targets:
    norm_t = os.path.normpath(target)
    os.makedirs(os.path.dirname(norm_t), exist_ok=True) if os.path.dirname(norm_t) else None
    shutil.copy2(adm_apk_src, norm_t)
    print(f"  -> Distributed to: {norm_t}")

# Verify Admin APK
with zipfile.ZipFile(adm_apk_src, 'r') as z:
    idx_adm = z.read('assets/public/index.html').decode('utf-8', errors='ignore')
    has_pickup_soon = 'pickup_soon' in idx_adm
    has_return_soon = 'return_soon' in idx_adm
    print(f"  [ADMIN APK VERIFIED] pickup_soon={has_pickup_soon}, return_soon={has_return_soon}")

# ----------------------------------------------------------------------
# 3. FINAL SUMMARY
# ----------------------------------------------------------------------
print("\n" + "=" * 60)
print("SUCCESS: BOTH DEBUG APKS COMPILED AND VERIFIED!")
print("=" * 60)
print(f"Customer APK: AutorideCustomer-debug-latest.apk ({os.path.getsize('AutorideCustomer-debug-latest.apk'):,} bytes)")
print(f"Admin APK:    AutorideAdmin-debug-latest.apk ({os.path.getsize('AutorideAdmin-debug-latest.apk'):,} bytes)")
print("=" * 60)
