with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
for m in re.finditer(r'\.page\s*\{([^}]+)\}', text):
    print('.page rule:', m.group(1).strip().replace('\n', ' '))

for m in re.finditer(r'\.header\s*\{([^}]+)\}', text):
    print('.header rule:', m.group(1).strip().replace('\n', ' '))

for m in re.finditer(r'@media[^{]+landscape[^{]*\{', text):
    print('landscape media query:', m.group(0))
