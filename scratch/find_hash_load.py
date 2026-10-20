with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Find hash listener or page load hash handling
for m in re.finditer(r'location\.hash|hashchange|DOMContentLoaded|window\.onload', text):
    start = max(0, m.start() - 50)
    end = min(len(text), m.end() + 200)
    print("Match at char", m.start())
    print(text[start:end])
    print("="*40)
