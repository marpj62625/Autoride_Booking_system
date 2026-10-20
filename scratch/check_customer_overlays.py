with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'id="overlay-checkout"' in line or 'id="overlay-vehicle-details"' in line or 'bottom-bar' in line:
            print(f'{i+1}: {line.strip()[:100]}')
