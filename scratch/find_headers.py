with open('admin_app/index.html', encoding='utf-8') as f:
    text = f.read()

import re
headers = re.findall(r"headers:\s*\{([^}]+)\}", text)
print(f"Found {len(headers)} headers definitions:")
for h in headers[:10]:
    print(" ", h.strip().replace('\n', ' '))
