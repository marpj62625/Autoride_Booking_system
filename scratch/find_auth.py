with open('admin_app/index.html', encoding='utf-8') as f:
    text = f.read()

import re
m = re.findall(r"(?:admin_id|currentUser|localStorage\.getItem\(['\"][a-zA-Z0-9_-]+['\"]\))", text)
print("Auth references in admin_app:")
for x in set(m):
    print(" ", x)
