with open('customer_mobile/www/style.css', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print("Checking containers in style.css:")
for m in re.finditer(r'\.(container|main|content|card|header|bottom-nav|nav)[^{]*\{[^}]+\}', text):
    snippet = m.group(0).replace('\n', ' ')
    if len(snippet) > 100:
        snippet = snippet[:100] + '...'
    print(" ", snippet)
