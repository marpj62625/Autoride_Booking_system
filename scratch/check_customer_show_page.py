with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
m = re.search(r'function\s+showPage\s*\([^)]*\)\s*\{', text)
if m:
    print(text[m.start():m.start()+600])
