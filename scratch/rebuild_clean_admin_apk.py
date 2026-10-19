import os
import shutil
import subprocess

print("Step 1: Stopping Gradle Daemons...")
subprocess.run(['gradlew.bat', '--stop'], cwd='admin_mobile/android', shell=True)

print("\nStep 2: Cleaning unnecessary heavy files from admin_mobile/www...")
www_node_modules = 'admin_mobile/www/node_modules'
if os.path.exists(www_node_modules):
    print("Removing admin_mobile/www/node_modules...")
    shutil.rmtree(www_node_modules, ignore_errors=True)

for f in os.listdir('admin_mobile/www'):
    if f.endswith('.apk'):
        apk_p = os.path.join('admin_mobile/www', f)
        print(f"Removing bundled APK from www: {apk_p}")
        os.remove(apk_p)

print("\nStep 3: Cleaning heavy files from android assets public...")
assets_public = 'admin_mobile/android/app/src/main/assets/public'
if os.path.exists(os.path.join(assets_public, 'node_modules')):
    print("Removing assets/public/node_modules...")
    shutil.rmtree(os.path.join(assets_public, 'node_modules'), ignore_errors=True)

for f in os.listdir(assets_public):
    if f.endswith('.apk'):
        apk_p = os.path.join(assets_public, f)
        print(f"Removing bundled APK from assets public: {apk_p}")
        os.remove(apk_p)

print("\nStep 4: Ensuring admin_mobile/www/index.html matches admin_app/index.html...")
shutil.copy2('admin_app/index.html', 'admin_mobile/www/index.html')

print("\nStep 5: Running npx cap copy android...")
subprocess.run('npx cap copy android', cwd='admin_mobile', shell=True, check=True)

env = os.environ.copy()
env['JAVA_HOME'] = r'C:\Users\patri\scoop\apps\openjdk21\current'
env['ANDROID_HOME'] = r'C:\Users\patri\AppData\Local\Android\Sdk'
env['PATH'] = os.path.join(env['JAVA_HOME'], 'bin') + os.pathsep + env['PATH']

print("\nStep 6: Running gradlew assembleDebug...")
# Note: we use --rerun-tasks to ensure all packaging tasks actually execute and do not use stale cache
res = subprocess.run(['gradlew.bat', 'assembleDebug', '--rerun-tasks'], cwd='admin_mobile/android', shell=True, env=env, capture_output=True, text=True)
print("Gradle Returncode:", res.returncode)
if res.returncode != 0:
    print("STDERR:", res.stderr[-1000:])
    print("STDOUT:", res.stdout[-1000:])
    raise RuntimeError("Admin APK build failed")
else:
    print("Gradle build successful!")

adm_apk_src = r'C:\Users\patri\.autoride_builds\admin\app\outputs\apk\debug\app-debug.apk'
if not os.path.exists(adm_apk_src):
    alt = r'admin_mobile\android\app\build\outputs\apk\debug\app-debug.apk'
    if os.path.exists(alt):
        adm_apk_src = alt

print(f"\n[SUCCESS] Admin APK compiled: {adm_apk_src}")
adm_targets = [
    'AutorideAdmin-debug-latest.apk',
    'AutorideAdmin-debug.apk',
    'admin_mobile/AutorideAdmin-debug-latest.apk',
    'admin_mobile/AutorideAdmin-debug.apk',
    'admin_app/AutorideAdmin-debug-latest.apk',
    'admin_mobile/android/app/build/outputs/apk/debug/app-debug.apk',
]
for t in adm_targets:
    norm_t = os.path.normpath(t)
    os.makedirs(os.path.dirname(norm_t), exist_ok=True) if os.path.dirname(norm_t) else None
    shutil.copy2(adm_apk_src, norm_t)
    print(f"  -> Distributed to: {norm_t}")

print(f"\nDone. Admin APK size: {os.path.getsize(adm_apk_src):,} bytes")
