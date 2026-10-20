import sys

CUST_JS = 'AutorideSystem/customer_mobile/www/js/app.js'

with open(CUST_JS, 'r', encoding='utf-8') as f:
    content = f.read()

target = '<input type="number" id="inspMileage" placeholder="e.g. 12500">'
replacement = '<input type="number" id="inspMileage" min="0" max="999999" placeholder="e.g. 12500">'

if content.count(target) != 1:
    print(f"ERROR: Found {content.count(target)} occurrences of target in customer app.js")
    sys.exit(1)

content = content.replace(target, replacement, 1)

with open(CUST_JS, 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: Patched inspMileage bounds in customer_mobile/www/js/app.js")
