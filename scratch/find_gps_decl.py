with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'const GPS = {' in line or 'window.GPS = {' in line or 'var GPS = {' in line:
        print(f'{i+1}: {line.strip()[:100]}')
    if 'GPS = {' in line:
        print(f'{i+1}: {line.strip()[:100]}')
