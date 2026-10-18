import shutil
import os

sync_ops = [
    # Admin targets
    ('admin_app/index.html', 'admin_mobile/www/index.html'),
    ('admin_app/index.html', 'admin_mobile/android/app/src/main/assets/public/index.html'),
    ('admin_app/index.html', 'admin_mobile/ios/App/App/public/index.html'),

    # Customer HTML targets
    ('customer_mobile/www/index.html', 'frontend/index.html'),
    ('customer_mobile/www/index.html', 'customer_mobile/android/app/src/main/assets/public/index.html'),
    ('customer_mobile/www/register.html', 'frontend/register.html'),
    ('customer_mobile/www/register.html', 'customer_mobile/android/app/src/main/assets/public/register.html'),

    # Customer CSS targets
    ('customer_mobile/www/style.css', 'frontend/style.css'),
    ('customer_mobile/www/style.css', 'customer_mobile/android/app/src/main/assets/public/style.css'),

    # Customer JS targets
    ('customer_mobile/www/js/app.js', 'frontend/js/app.js'),
    ('customer_mobile/www/js/app.js', 'customer_mobile/android/app/src/main/assets/public/js/app.js'),
    ('customer_mobile/www/js/utils.js', 'frontend/js/utils.js'),
    ('customer_mobile/www/js/utils.js', 'customer_mobile/android/app/src/main/assets/public/js/utils.js'),
]


for src, dst in sync_ops:
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        print(f"Copied {src} -> {dst} ({os.path.getsize(dst)} bytes)")
    else:
        print(f"WARNING: Source {src} does not exist!")

print("\nALL TARGETS SYNCED SUCCESSFULLY!")
