import os
import shutil
import subprocess
import zipfile
import time

print("=" * 70)
print("AUTORIDE: COMPILING FRESH DEBUG APKS FOR CUSTOMER AND ADMIN")
print("=" * 70)

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
root_dir = os.path.abspath(os.path.join(base_dir, '..'))

env = os.environ.copy()
env['JAVA_HOME'] = r'C:\Users\patri\scoop\apps\openjdk21\current'
env['ANDROID_HOME'] = r'C:\Users\patri\AppData\Local\Android\Sdk'
env['PATH'] = os.path.join(env['JAVA_HOME'], 'bin') + os.pathsep + env['PATH']

print(f"Base Dir: {base_dir}")
print(f"Root Dir: {root_dir}")
print(f"JAVA_HOME: {env['JAVA_HOME']}")
print(f"ANDROID_HOME: {env['ANDROID_HOME']}")

# ----------------------------------------------------------------------
# 1. BUILD CUSTOMER DEBUG APK
# ----------------------------------------------------------------------
print("\n" + "-" * 50)
print("[1/2] PREPARING & COMPILING CUSTOMER DEBUG APK")
print("-" * 50)

# Sync customer web assets from frontend -> customer_mobile/www -> android assets
frontend_dir = os.path.join(base_dir, 'frontend')
cm_dir = os.path.join(base_dir, 'customer_mobile')
cm_www = os.path.join(cm_dir, 'www')
cm_assets = os.path.join(cm_dir, 'android', 'app', 'src', 'main', 'assets', 'public')

for rel_path in ['index.html', os.path.join('js', 'app.js'), os.path.join('js', 'utils.js'), os.path.join('css', 'style.css')]:
    src_f = os.path.join(frontend_dir, rel_path)
    if os.path.exists(src_f):
        sync_roots = [cm_www, cm_assets]
        root_candidate = os.path.join(root_dir, rel_path)
        if os.path.exists(root_candidate):
            sync_roots.append(root_dir)
        for dst_root in sync_roots:
            dst_f = os.path.join(dst_root, rel_path)
            os.makedirs(os.path.dirname(dst_f), exist_ok=True)
            shutil.copy2(src_f, dst_f)
        print(f"Synced {rel_path} from frontend -> customer_mobile/www & android assets")

if os.path.exists(cm_www) and os.path.exists(cm_assets):
    for root, dirs, files in os.walk(cm_www):
        rel = os.path.relpath(root, cm_www)
        target_dir = os.path.normpath(os.path.join(cm_assets, rel))
        os.makedirs(target_dir, exist_ok=True)
        for f in files:
            if f.endswith('.apk') or f.endswith('.tmp') or 'node_modules' in root:
                continue
            shutil.copy2(os.path.join(root, f), os.path.join(target_dir, f))
    print(f"Synced customer assets: {cm_www} -> {cm_assets}")

# Stop gradle daemons in customer
subprocess.run(['gradlew.bat', '--stop'], cwd=os.path.join(cm_dir, 'android'), shell=True, env=env, capture_output=True)

# Remove any old customer debug apk
old_cust_apks = [
    r'C:\Users\patri\.autoride_builds\customer\app\outputs\apk\debug\app-debug.apk',
    os.path.join(cm_dir, 'android', 'app', 'build', 'outputs', 'apk', 'debug', 'app-debug.apk')
]
for p in old_cust_apks:
    if os.path.exists(p):
        try:
            os.remove(p)
            print(f"Removed previous customer apk: {p}")
        except Exception as e:
            print(f"Could not remove {p}: {e}")

print("Running customer Gradle build (clean assembleDebug --rerun-tasks)...")
cust_grad = subprocess.run(
    ['gradlew.bat', 'clean', 'assembleDebug', '--rerun-tasks', '--no-daemon'],
    cwd=os.path.join(cm_dir, 'android'),
    shell=True,
    env=env,
    capture_output=True,
    text=True
)

cust_apk_src = r'C:\Users\patri\.autoride_builds\customer\app\outputs\apk\debug\app-debug.apk'
if not os.path.exists(cust_apk_src):
    alt = os.path.join(cm_dir, 'android', 'app', 'build', 'outputs', 'apk', 'debug', 'app-debug.apk')
    if os.path.exists(alt):
        cust_apk_src = alt

if cust_grad.returncode != 0 or not os.path.exists(cust_apk_src):
    print("CUSTOMER GRADLE BUILD FAILED!")
    print("STDOUT:", cust_grad.stdout[-1500:])
    print("STDERR:", cust_grad.stderr[-1500:])
    raise RuntimeError("Customer build failed")

print(f"[SUCCESS] Customer APK compiled: {cust_apk_src}")
print(f"Size: {os.path.getsize(cust_apk_src):,} bytes | Built: {time.ctime(os.path.getmtime(cust_apk_src))}")

# Distribute Customer APK
cust_targets = [
    os.path.join(root_dir, 'AutorideCustomer-debug-latest.apk'),
    os.path.join(root_dir, 'AutorideCustomer-debug.apk'),
    os.path.join(root_dir, 'autoride-customer-debug-latest.apk'),
    os.path.join(root_dir, 'autoride-customer-debug.apk'),
    os.path.join(root_dir, 'customer_mobile', 'autoride-customer-debug-latest.apk'),
    os.path.join(root_dir, 'customer_mobile', 'AutorideCustomer-debug-latest.apk'),
    os.path.join(root_dir, 'customer_mobile', 'AutorideCustomer-debug.apk'),
    os.path.join(base_dir, 'AutorideCustomer-debug-latest.apk'),
    os.path.join(base_dir, 'AutorideCustomer-debug.apk'),
    os.path.join(base_dir, 'autoride-customer-debug-latest.apk'),
    os.path.join(base_dir, 'autoride-customer-debug.apk'),
    os.path.join(cm_dir, 'AutorideCustomer-debug-latest.apk'),
    os.path.join(cm_dir, 'AutorideCustomer-debug.apk'),
    os.path.join(cm_dir, 'autoride-customer-debug-latest.apk'),
    os.path.join(cm_dir, 'android', 'app', 'build', 'outputs', 'apk', 'debug', 'app-debug.apk'),
]
for target in cust_targets:
    target = os.path.normpath(target)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    shutil.copy2(cust_apk_src, target)

print(f"Distributed Customer APK to {len(cust_targets)} targets.")

# Verify Customer APK
with zipfile.ZipFile(cust_apk_src, 'r') as z:
    idx_cust = z.read('assets/public/index.html').decode('utf-8', errors='ignore')
    appjs_cust = z.read('assets/public/js/app.js').decode('utf-8', errors='ignore')
    has_cam = 'Take Selfie' in idx_cust
    has_rate = 'vd-rate-action-box' in idx_cust
    has_clear = 'clearAllCustomerFieldsAndState' in appjs_cust
    print(f"Customer APK Verification: Take Selfie={has_cam}, vd-rate-action-box={has_rate}, clearAllCustomerFieldsAndState={has_clear}")
    if not has_clear:
        raise RuntimeError("Customer APK missing clearAllCustomerFieldsAndState!")


# ----------------------------------------------------------------------
# 2. BUILD ADMIN DEBUG APK
# ----------------------------------------------------------------------
print("\n" + "-" * 50)
print("[2/2] PREPARING & COMPILING ADMIN DEBUG APK")
print("-" * 50)

adm_dir = os.path.join(base_dir, 'admin_mobile')
adm_app_dir = os.path.join(base_dir, 'admin_app')
adm_www = os.path.join(adm_dir, 'www')
adm_assets = os.path.join(adm_dir, 'android', 'app', 'src', 'main', 'assets', 'public')

# Sync admin files from admin_app
for fname in ['index.html', 'desktop.css']:
    src_f = os.path.join(adm_app_dir, fname)
    dst_www = os.path.join(adm_www, fname)
    dst_assets = os.path.join(adm_assets, fname)
    if os.path.exists(src_f):
        shutil.copy2(src_f, dst_www)
        shutil.copy2(src_f, dst_assets)
        print(f"Synced {fname} from admin_app -> www & android assets")

# Clean node_modules and .apk in assets
for p in [os.path.join(adm_www, 'node_modules'), os.path.join(adm_assets, 'node_modules')]:
    if os.path.exists(p):
        shutil.rmtree(p, ignore_errors=True)

for folder in [adm_www, adm_assets]:
    if os.path.exists(folder):
        for f in os.listdir(folder):
            if f.endswith('.apk'):
                os.remove(os.path.join(folder, f))

# Stop gradle daemons in admin
subprocess.run(['gradlew.bat', '--stop'], cwd=os.path.join(adm_dir, 'android'), shell=True, env=env, capture_output=True)

# Remove old admin apk
old_adm_apks = [
    r'C:\Users\patri\.autoride_builds\admin\app\outputs\apk\debug\app-debug.apk',
    os.path.join(adm_dir, 'android', 'app', 'build', 'outputs', 'apk', 'debug', 'app-debug.apk')
]
for p in old_adm_apks:
    if os.path.exists(p):
        try:
            os.remove(p)
            print(f"Removed previous admin apk: {p}")
        except Exception as e:
            print(f"Could not remove {p}: {e}")

print("Running admin Gradle build (clean assembleDebug --rerun-tasks)...")
adm_grad = subprocess.run(
    ['gradlew.bat', 'clean', 'assembleDebug', '--rerun-tasks', '--no-daemon'],
    cwd=os.path.join(adm_dir, 'android'),
    shell=True,
    env=env,
    capture_output=True,
    text=True
)

adm_apk_src = r'C:\Users\patri\.autoride_builds\admin\app\outputs\apk\debug\app-debug.apk'
if not os.path.exists(adm_apk_src):
    alt = os.path.join(adm_dir, 'android', 'app', 'build', 'outputs', 'apk', 'debug', 'app-debug.apk')
    if os.path.exists(alt):
        adm_apk_src = alt

if adm_grad.returncode != 0 or not os.path.exists(adm_apk_src):
    print("ADMIN GRADLE BUILD FAILED!")
    print("STDOUT:", adm_grad.stdout[-1500:])
    print("STDERR:", adm_grad.stderr[-1500:])
    raise RuntimeError("Admin build failed")

print(f"[SUCCESS] Admin APK compiled: {adm_apk_src}")
print(f"Size: {os.path.getsize(adm_apk_src):,} bytes | Built: {time.ctime(os.path.getmtime(adm_apk_src))}")

# Distribute Admin APK
adm_targets = [
    os.path.join(root_dir, 'AutorideAdmin-debug-latest.apk'),
    os.path.join(root_dir, 'AutorideAdmin-debug.apk'),
    os.path.join(root_dir, 'autoride-admin-debug-latest.apk'),
    os.path.join(root_dir, 'autoride-admin-debug.apk'),
    os.path.join(base_dir, 'AutorideAdmin-debug-latest.apk'),
    os.path.join(base_dir, 'AutorideAdmin-debug.apk'),
    os.path.join(base_dir, 'autoride-admin-debug-latest.apk'),
    os.path.join(base_dir, 'autoride-admin-debug.apk'),
    os.path.join(adm_dir, 'AutorideAdmin-debug-latest.apk'),
    os.path.join(adm_dir, 'AutorideAdmin-debug.apk'),
    os.path.join(adm_dir, 'autoride-admin-debug-latest.apk'),
    os.path.join(adm_app_dir, 'AutorideAdmin-debug-latest.apk'),
    os.path.join(adm_dir, 'android', 'app', 'build', 'outputs', 'apk', 'debug', 'app-debug.apk'),
]
for target in adm_targets:
    target = os.path.normpath(target)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    shutil.copy2(adm_apk_src, target)

print(f"Distributed Admin APK to {len(adm_targets)} targets.")

# Verify Admin APK
with zipfile.ZipFile(adm_apk_src, 'r') as z:
    idx_adm = z.read('assets/public/index.html').decode('utf-8', errors='ignore')
    css_adm = z.read('assets/public/desktop.css').decode('utf-8', errors='ignore')
    has_super_admin_bypass = 'lockPerm' in idx_adm and 'super_admin' in idx_adm
    has_fluid_settings = 'settings-layout-container' in idx_adm
    has_nav_activity = "navTo('activity')" in idx_adm
    print(f"Admin APK Verification: super_admin_bypass={has_super_admin_bypass}, fluid_settings={has_fluid_settings}, navTo('activity')={has_nav_activity}")

print("\n" + "=" * 70)
print("ALL DEBUG APKS COMPILED & DISTRIBUTED SUCCESSFULLY!")
print("=" * 70)
print(f"Customer APK : {os.path.getsize(os.path.join(root_dir, 'AutorideCustomer-debug-latest.apk')):,} bytes")
print(f"Admin APK    : {os.path.getsize(os.path.join(root_dir, 'AutorideAdmin-debug-latest.apk')):,} bytes")
