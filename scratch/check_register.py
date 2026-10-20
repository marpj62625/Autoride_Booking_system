with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = list(re.finditer(r'id=[\"\']page-register[\"\']', text))
print('Count:', len(matches))
for m in matches:
    pos = m.start()
    print(text[pos:pos+1500])
