with open('customer_mobile/www/js/app.js', 'r', encoding='latin-1') as f:
    content = f.read()

content = content.replace('\nfunction selectPayMethod(method, el) {', '\nfunction selectPayMethod(method, el) {')
content = content.replace('\\nfunction selectPayMethod(method, el) {', '\nfunction selectPayMethod(method, el) {')

with open('customer_mobile/www/js/app.js', 'w', encoding='latin-1') as f:
    f.write(content)
