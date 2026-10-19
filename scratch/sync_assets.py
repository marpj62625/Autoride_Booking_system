import shutil
import hashlib
import os

files_to_sync = [
    ('frontend/index.html', [
        'customer_mobile/www/index.html',
        'customer_mobile/android/app/src/main/assets/public/index.html'
    ]),
    ('frontend/js/app.js', [
        'customer_mobile/www/js/app.js',
        'customer_mobile/android/app/src/main/assets/public/js/app.js'
    ])
]

def hash_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

print("Syncing assets...")
for src, targets in files_to_sync:
    src_hash = hash_file(src)
    print(f"Source: {src} ({src_hash[:12]})")
    for dst in targets:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        dst_hash = hash_file(dst)
        assert src_hash == dst_hash, f"Hash mismatch between {src} and {dst}!"
        print(f"  -> Synced to: {dst} (MATCH)")

print("\nALL ASSETS SYNCED AND VERIFIED!")
