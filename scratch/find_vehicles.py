with open('admin_app/index.html', encoding='utf-8') as f:
    text = f.read()

import re
v_fetches = re.findall(r"fetch\([`'\"]([^`'\"]*vehicle[^`'\"]*)[`'\"]", text, re.IGNORECASE)
print("Vehicle fetches in admin_app:")
for f in set(v_fetches):
    print(" ", f)
