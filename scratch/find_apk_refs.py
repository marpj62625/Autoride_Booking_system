import re

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("APK references in admin_app/index.html:")
for i, line in enumerate(text.splitlines()):
    if '.apk' in line.lower():
        print(f"Line {i+1}: {line.strip()[:140]}")
