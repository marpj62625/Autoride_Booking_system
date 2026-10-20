with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'blynkMapFrame' in line or 'id="gps"' in line:
            print(f'{i+1}: {line.strip()[:100]}')
