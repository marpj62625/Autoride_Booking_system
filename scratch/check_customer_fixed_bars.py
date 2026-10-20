with open('customer_mobile/www/checkout.html', 'r', encoding='utf-8') as f:
    text_co = f.read()

with open('customer_mobile/www/vehicle-details.html', 'r', encoding='utf-8') as f:
    text_vd = f.read()

import re
for name, t in [('checkout', text_co), ('vehicle-details', text_vd)]:
    print(f'=== {name} ===')
    for m in re.finditer(r'position:\s*fixed[^;]+;|bottom:\s*0', t):
        start = max(0, m.start() - 50)
        end = min(len(t), m.end() + 100)
        print('  ' + t[start:end].replace('\n', ' '))
