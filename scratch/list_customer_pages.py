with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'overlay-page' in line or 'class="page' in line:
            print(f'{i+1}: {line.strip()[:100]}')
