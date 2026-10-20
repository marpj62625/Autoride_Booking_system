with open('admin_mobile/android/app/src/main/assets/public/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'<button[^>]+class=[\'"]nb-chip[^>]*>.*?</button>', text)
print('nb-chips count in assets/public:', len(matches))
for m in matches:
    print(' ', m[:100])
