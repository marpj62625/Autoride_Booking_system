with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    text = f.read()
print('landscape in index.html:', 'landscape' in text)
with open('customer_mobile/www/style.css', 'r', encoding='utf-8') as f:
    text2 = f.read()
print('landscape in style.css:', 'landscape' in text2)
