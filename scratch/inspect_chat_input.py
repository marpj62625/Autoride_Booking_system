with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'class=["\']ac-input-bar["\']|id=["\']acInput["\']', text)]
for idx, pos in enumerate(matches):
    print(f"Match {idx+1}:")
    print(" " + text[pos-50:pos+250].replace('\n', ' '))
