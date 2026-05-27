with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

lines = content.splitlines()
for i, line in enumerate(lines, 1):
    if 'license' in line.lower() and ('fetch' in line or 'api' in line.lower() or 'booking' in line.lower()):
        print(f"Line {i}: {line.strip()[:200]}")
