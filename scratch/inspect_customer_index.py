with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines[:1200]):
    if 'bottom-nav' in line or 'bottom_nav' in line or '<nav' in line or 'page-home' in line or 'id="page' in line:
        print(f'{i+1}: {line.strip()[:100]}')
