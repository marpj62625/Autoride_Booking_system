import os

files_to_check = [
    'admin_app/index.html',
    'admin_mobile/www/index.html',
    'admin_mobile/android/app/src/main/assets/public/index.html',
    'admin_mobile/ios/App/App/public/index.html',
    'customer_mobile/www/index.html',
    'customer_mobile/android/app/src/main/assets/public/index.html',
    'frontend/index.html',
    'customer_mobile/www/js/app.js',
    'frontend/js/app.js',
    'customer_mobile/android/app/src/main/assets/public/js/app.js',
    'customer_mobile/www/style.css',
    'frontend/style.css',
    'customer_mobile/android/app/src/main/assets/public/style.css'
]

errors = []
for p in files_to_check:
    if not os.path.exists(p):
        errors.append(f"MISSING: {p}")
        continue
    with open(p, 'r', encoding='utf-8') as f:
        data = f.read()
    if len(data) == 0:
        errors.append(f"EMPTY: {p}")
    else:
        print(f"OK: {p} ({len(data):,} bytes)")

if errors:
    print("ERRORS FOUND:")
    for e in errors:
        print("  ", e)
else:
    print("\nALL FILES VERIFIED & PRESENT!")
