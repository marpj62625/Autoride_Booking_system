with open('customer_mobile/www/js/app.js', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if any(k in line for k in ['function showPage(', 'showPage(\'home\'', 'showPage("home"', 'function checkAuth(', 'DOMContentLoaded']):
            print(f'{i+1}: {line.strip()[:100]}')
