import shutil
import os
import hashlib

def sha256(fname):
    h = hashlib.sha256()
    with open(fname, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

src = 'frontend/js/app.js'
destinations = [
    'customer_mobile/www/js/app.js',
    'customer_mobile/android/app/src/main/assets/public/js/app.js'
]

print(f"Source: {src} (sha256: {sha256(src)[:12]})")
for dest in destinations:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(src, dest)
    print(f"  Copied to {dest} (sha256: {sha256(dest)[:12]}) -> MATCH: {sha256(src) == sha256(dest)}")
