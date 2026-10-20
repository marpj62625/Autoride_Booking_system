for fn in ['checkout.html', 'vehicle-details.html']:
    with open('customer_mobile/www/' + fn, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if 'fixed' in line and 'bottom' in line:
                print(f'{fn}:{i+1}: {line.strip()[:100]}')
