with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    text_cm_idx = f.read()

with open('customer_mobile/www/style.css', 'r', encoding='utf-8') as f:
    text_cm_css = f.read()

import re
print("index.html .page rules:")
for m in re.finditer(r'\.page\s*\{([^}]+)\}', text_cm_idx):
    print(" ", m.group(0).replace('\n', ' '))

print("style.css .page rules:")
for m in re.finditer(r'\.page\s*\{([^}]+)\}', text_cm_css):
    print(" ", m.group(0).replace('\n', ' '))
