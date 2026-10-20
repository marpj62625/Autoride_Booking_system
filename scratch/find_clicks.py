with open('frontend/js/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'(\w+\.addEventListener\([\'"]click[\'"].*?\n.*?\{)', text)
for m in matches:
    print('CLICK LISTENER:', m)
