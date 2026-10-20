with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
for m in re.finditer(r'\.(page-header|app-header|header)\s*\{([^}]+)\}', text):
    print(m.group(0).replace('\n', ' '))
