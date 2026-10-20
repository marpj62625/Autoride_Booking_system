with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if ('const API_URL' in line or 'var API_URL' in line or 'let API_URL' in line or
        'const API_BASE' in line or 'var API_BASE' in line or 'let API_BASE' in line or
        'window.API_BASE' in line or 'window.API_URL' in line):
        print(f"Line {i+1}: {line.strip()}")
        for j in range(max(0, i-5), min(len(lines), i+15)):
            print(f"  {j+1}: {repr(lines[j])}")
