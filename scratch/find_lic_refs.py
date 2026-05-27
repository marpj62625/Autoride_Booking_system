with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

lines = content.splitlines()
for i, line in enumerate(lines, 1):
    if 'license-details' in line:
        print(f"Line {i}: {line.strip()[:200]}")
