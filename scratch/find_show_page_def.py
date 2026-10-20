with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
for m in re.finditer(r'showPage\s*=\s*function|\bfunction\s+showPage\b|showPage\s*\(', text):
    start = max(0, m.start() - 20)
    end = min(len(text), m.end() + 200)
    snippet = text[start:end]
    if 'onclick' not in snippet and 'href' not in snippet:
        print(f"Match at {m.start()}: {snippet[:150]}")
