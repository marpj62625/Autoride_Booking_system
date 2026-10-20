with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

m = re.search(r'id=["\']sidebarToggleBtn["\']', text)
if m:
    print(text[m.start()-50:m.start()+250])
