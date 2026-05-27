with open('customer_mobile/www/js/app.js', 'r', encoding='latin-1') as f:
    content = f.read()

# Find all occurrences of /api/user/license or /api/api
lines = content.splitlines()
for i, line in enumerate(lines, 1):
    if '/api/user/license' in line or '/api/api/' in line:
        print(f"Line {i}: {line.strip()[:200]}")
