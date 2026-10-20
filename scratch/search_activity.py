with open('admin_app/index.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'activity' in line.lower() and ('tab' in line.lower() or 'filter' in line.lower() or 'log' in line.lower() or 'page 1 of' in line.lower()):
        print(f"{i+1}: {line.strip()[:120]}")
