with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

for m in re.finditer(r'touchmove|preventDefault|overflow', text):
    start = max(0, m.start() - 30)
    end = min(len(text), m.end() + 70)
    snippet = text[start:end].replace('\n', ' ')
    if 'touchmove' in snippet or 'preventDefault' in snippet:
        print(f"Match at {m.start()}: {snippet}")
