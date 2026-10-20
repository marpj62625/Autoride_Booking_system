with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
for m in re.finditer(r'page-home', text):
    start = max(0, m.start() - 50)
    end = min(len(text), m.end() + 100)
    # Check if inside script
    if '<script' in text[:m.start()] and '</script>' in text[m.end():]:
        print(text[start:end])
        print('---')
