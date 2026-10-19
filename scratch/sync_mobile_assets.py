import os
import shutil

sync_tasks = [
    ('admin_app/index.html', 'admin_mobile/www/index.html'),
    ('admin_app/index.html', 'admin_mobile/android/app/src/main/assets/public/index.html'),
    ('admin_app/index.html', 'admin_mobile/ios/App/App/public/index.html'),
    ('admin_app/desktop.css', 'admin_mobile/www/desktop.css'),
    ('admin_app/desktop.css', 'admin_mobile/android/app/src/main/assets/public/desktop.css'),
]

for src, dst in sync_tasks:
    if os.path.exists(src):
        dst_dir = os.path.dirname(dst)
        if os.path.exists(dst_dir):
            shutil.copy2(src, dst)
            print(f"Synced {src} -> {dst}")
        else:
            print(f"Directory {dst_dir} does not exist, skipping {dst}")

# Customer mobile www to android assets
cm_www = 'customer_mobile/www'
cm_android = 'customer_mobile/android/app/src/main/assets/public'
if os.path.exists(cm_android):
    for f in ['index.html', 'style.css', 'js/app.js']:
        src_f = os.path.join(cm_www, f)
        dst_f = os.path.join(cm_android, f)
        if os.path.exists(src_f):
            os.makedirs(os.path.dirname(dst_f), exist_ok=True)
            shutil.copy2(src_f, dst_f)
            print(f"Synced {src_f} -> {dst_f}")
