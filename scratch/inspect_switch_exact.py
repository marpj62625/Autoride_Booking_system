with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
m = re.search(r"if\s*\(\s*tabId\s*===\s*'fleet-calendar'[^)]*\)", text)
if m:
    start = max(0, m.start() - 100)
    end = min(len(text), m.end() + 200)
    print("Exact snippet:")
    print(repr(text[start:end]))
