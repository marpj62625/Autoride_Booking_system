with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'showPage', text)]
print('showPage count:', len(matches))
for m in re.finditer(r'function\s+showPage[^{]*\{', text):
    print('Function match:', text[m.start():m.start()+200])

for m in re.finditer(r'window\.showPage\s*=', text):
    print('Window match:', text[m.start():m.start()+200])

for m in re.finditer(r'const\s+showPage\s*=', text):
    print('Const match:', text[m.start():m.start()+200])
