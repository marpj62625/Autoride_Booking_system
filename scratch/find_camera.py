import re

for fn in ['frontend/index.html', 'frontend/js/app.js']:
    with open(fn, 'r', encoding='utf-8') as f:
        content = f.read()
    print('=== FILE:', fn)
    for m in re.finditer(r'([^\n]*camera[^\n]*)', content, re.IGNORECASE):
        print(m.group(1).strip()[:140])
