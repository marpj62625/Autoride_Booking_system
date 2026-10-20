with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text_app = f.read()

with open('admin_mobile/www/index.html', 'r', encoding='utf-8') as f:
    text_mob = f.read()

import re
m_app = re.findall(r'API_BASE\s*=\s*[^;]+;', text_app)
m_mob = re.findall(r'API_BASE\s*=\s*[^;]+;', text_mob)

print("API_BASE in app:", m_app[:3])
print("API_BASE in mob:", m_mob[:3])
