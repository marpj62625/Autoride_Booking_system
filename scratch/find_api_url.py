import re

with open('admin_mobile/www/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

for i, line in enumerate(text.splitlines()):
    if 'API_URL' in line or 'API_BASE' in line or 'apiUrl' in line:
        if '=' in line or 'const' in line or 'let' in line or 'var' in line:
            print(f"Line {i+1}: {line.strip()}")
