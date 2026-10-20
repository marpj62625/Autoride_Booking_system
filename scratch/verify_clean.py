import re

files_to_check = [
    'admin_app/index.html',
    'admin_mobile/www/index.html',
    'admin_mobile/android/app/src/main/assets/public/index.html',
    'customer_mobile/www/index.html',
    'frontend/index.html',
    'customer_mobile/android/app/src/main/assets/public/index.html',
    'customer_mobile/www/js/app.js',
    'frontend/js/app.js',
    'customer_mobile/android/app/src/main/assets/public/js/app.js',
]

errors = 0
for filepath in files_to_check:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content) < 100:
                print(f"ERROR: {filepath} is suspiciously small ({len(content)} bytes)")
                errors += 1
            else:
                print(f"OK: {filepath} ({len(content)} chars)")
    except Exception as e:
        print(f"ERROR reading {filepath}: {e}")
        errors += 1

if errors == 0:
    print("\nALL VERIFIED CLEAN!")
else:
    print(f"\nFOUND {errors} ERRORS!")
