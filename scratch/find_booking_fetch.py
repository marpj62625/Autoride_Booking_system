with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

lines = content.splitlines()
for i, line in enumerate(lines, 1):
    if 'admin/bookings' in line and 'license' in line:
        print(f"Line {i}: {line.strip()[:250]}")
    elif 'admin/bookings' in line and 'fetch' in line:
        print(f"Line {i}: {line.strip()[:250]}")
