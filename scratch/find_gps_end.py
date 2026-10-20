with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(23500, 23650):
    if i < len(lines):
        line = lines[i]
        if line.strip().startswith('};') or 'FleetCalendar' in line:
            print(f'{i+1}: {line.strip()[:80]}')
