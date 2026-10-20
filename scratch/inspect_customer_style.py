with open('customer_mobile/www/style.css', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if '@media' in line or 'bottom-nav' in line or '.page' in line or 'safe-area' in line:
        print(f'{i+1}: {line.strip()[:100]}')
