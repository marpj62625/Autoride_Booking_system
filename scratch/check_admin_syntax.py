import re
import subprocess
import tempfile
import os

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

scripts = re.findall(r'<script(?:\s+[^>]*)?>(.*?)</script>', content, re.DOTALL | re.IGNORECASE)
print(f"Found {len(scripts)} inline script tags in admin_app/index.html")

failed = False
for idx, script in enumerate(scripts):
    # Skip empty scripts or scripts with src
    if not script.strip():
        continue
    with tempfile.NamedTemporaryFile(suffix='.js', delete=False, mode='w', encoding='utf-8') as tf:
        tf.write(script)
        temp_path = tf.name

    try:
        res = subprocess.run(['node', '--check', temp_path], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"ERROR in script #{idx+1}:")
            print(res.stderr[:500])
            failed = True
        else:
            print(f"Script #{idx+1}: Syntax OK ({len(script)} chars)")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if not failed:
    print("ALL inline scripts in admin_app/index.html passed syntax check!")
else:
    raise SystemExit(1)
