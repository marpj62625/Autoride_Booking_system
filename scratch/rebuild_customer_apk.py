import os
import shutil
import subprocess
import zipfile
import time

print("=" * 60)
print("REBUILDING CUSTOMER DEBUG APK [v2026.10.19.8]")
print("=" * 60)

env = os.environ.copy()
env['JAVA_HOME'] = r'C:\Users\patri\scoop\apps\openjdk21\current'
env['ANDROID_HOME'] = r'C:\Users\patri\AppData\Local\Android\Sdk'
env['PATH'] = os.path.join(env['JAVA_HOME'], 'bin') + os.pathsep + env['PATH']

# Stop daemons
subprocess.run(['gradlew.bat', '--stop'], cwd='customer_mobile/android', shell=True, env=env, capture_output=True)

# Delete old APK from .autoride_builds and customer_mobile
for p in [
    r'C:\Users\patri\.autoride_builds\customer\app\outputs\apk\debug\app-debug.apk',
    r'customer_mobile\android\app\build\outputs\apk\debug\app-debug.apk',
]:
    if os.path.exists(p):
        os.remove(p)
        print(f"Removed old APK: {p}")

# Sync www to android assets
cm_www = 'customer_mobile/www'
cm_assets = 'customer_mobile/android/app/src/main/assets/public'
for root, dirs, files in os.walk(cm_www):
    rel = os.path.relpath(root, cm_www)
    target_dir = os.path.normpath(os.path.join(cm_assets, rel))
    os.makedirs(target_dir, exist_ok=True)
    for f in files:
        if f.endswith('.apk') or f.endswith('.tmp'):
            continue
        src_f = os.path.join(root, f)
        dst_f = os.path.join(target_dir, f)
        shutil.copy2(src_f, dst_f)

print(f"Synced {cm_www} -> {cm_assets}")

# Run gradle build
print("Compiling Customer Debug APK with Gradle (clean assembleDebug --rerun-tasks)...")
res = subprocess.run(
    ['gradlew.bat', 'clean', 'assembleDebug', '--rerun-tasks', '--no-daemon'],
    cwd='customer_mobile/android',
    shell=True,
    env=env,
    capture_output=True,
    text=True
)

cust_apk_src = r'C:\Users\patri\.autoride_builds\customer\app\outputs\apk\debug\app-debug.apk'
if not os.path.exists(cust_apk_src):
    alt = r'customer_mobile\android\app\build\outputs\apk\debug\app-debug.apk'
    if os.path.exists(alt):
        cust_apk_src = alt

if res.returncode != 0 or not os.path.exists(cust_apk_src):
    print("Gradle FAILED!")
    print("STDOUT:", res.stdout[-1500:])
    print("STDERR:", res.stderr[-1500:])
    raise RuntimeError("Build failed")

print(f"\n[SUCCESS] Customer APK compiled: {cust_apk_src}")
print(f"Size: {os.path.getsize(cust_apk_src):,} bytes, Compiled: {time.ctime(os.path.getmtime(cust_apk_src))}")

# Distribute Customer APK
targets = [
    'AutorideCustomer-debug-latest.apk',
    'AutorideCustomer-debug.apk',
    'customer_mobile/AutorideCustomer-debug-latest.apk',
    'customer_mobile/AutorideCustomer-debug.apk',
    'customer_mobile/android/app/build/outputs/apk/debug/app-debug.apk',
]
for t in targets:
    norm_t = os.path.normpath(t)
    os.makedirs(os.path.dirname(norm_t), exist_ok=True) if os.path.dirname(norm_t) else None
    shutil.copy2(cust_apk_src, norm_t)
    print(f"  -> Distributed to: {norm_t}")

# Verify inside APK
with zipfile.ZipFile(cust_apk_src, 'r') as z:
    idx = z.read('assets/public/index.html').decode('utf-8', errors='ignore')
    app_js = z.read('assets/public/js/app.js').decode('utf-8', errors='ignore')
    has_en_cam = 'Take Selfie' in idx and 'Face Here' in idx
    has_rate_box_css = 'vd-rate-action-box' in idx
    has_desktop_cam_html = 'desktopCameraModal' in idx
    has_desktop_cam_js = 'openDesktopCameraModal' in app_js
    print(f"\n[VERIFICATION]")
    print(f"  English camera in index.html: {has_en_cam}")
    print(f"  vd-rate-action-box CSS in index.html: {has_rate_box_css}")
    print(f"  desktopCameraModal in index.html: {has_desktop_cam_html}")
    print(f"  openDesktopCameraModal in app.js: {has_desktop_cam_js}")
    if not (has_en_cam and has_rate_box_css and has_desktop_cam_html and has_desktop_cam_js):
        raise ValueError("Verification failed: APK missing new fixes!")

print("\n" + "=" * 60)
print(f"CUSTOMER APK READY: AutorideCustomer-debug-latest.apk ({os.path.getsize('AutorideCustomer-debug-latest.apk'):,} bytes)")
print("=" * 60)
