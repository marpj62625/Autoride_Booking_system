with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'landscape' in line:
            print(f'{i+1}: {line.strip()[:100]}')
