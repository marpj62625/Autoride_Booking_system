import os, re

files = [
    'admin_app/index.html',
    'customer_mobile/www/index.html',
    'customer_mobile/www/js/app.js'
]

for fpath in files:
    if os.path.exists(fpath):
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            for idx, line in enumerate(f, 1):
                if 'type="file"' in line or "type='file'" in line:
                    print(f"{fpath}:{idx}: {line.strip()[:120]}")
