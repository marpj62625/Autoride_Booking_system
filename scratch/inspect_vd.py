with open('customer_mobile/www/vehicle-details.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'fixed' in line or 'bottom' in line or 'book' in line.lower() and 'button' in line.lower():
            if any(k in line for k in ['position', 'bottom', 'padding', 'btn', 'bar']):
                print(f'{i+1}: {line.strip()[:100]}')
