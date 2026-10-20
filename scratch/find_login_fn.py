with open('customer_mobile/www/js/app.js', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'function doLogin(' in line or 'function doRegister(' in line or 'localStorage.setItem(\'token\'' in line or 'localStorage.setItem("token"' in line:
            print(f'{i+1}: {line.strip()[:100]}')
