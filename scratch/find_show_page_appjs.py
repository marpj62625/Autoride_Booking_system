with open('customer_mobile/www/js/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
m = re.search(r'function\s+showPage\s*\([^)]*\)\s*\{', text)
if m:
    print('Found showPage in app.js at char:', m.start())
    lines = text[:m.start()].splitlines()
    print('Line:', len(lines)+1)
    print(text[m.start():m.start()+600])
