with open('customer_mobile/www/js/app.js', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'position: fixed' in line or 'position:fixed' in line:
            print(f'{i+1}: {line.strip()[:100]}')
