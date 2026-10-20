with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'adminLoginOverlay', text)]
for idx, pos in enumerate(matches):
    print(f"Match {idx+1} at {pos}:")
    print(repr(text[pos-40:pos+100]))
