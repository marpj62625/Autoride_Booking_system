with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
m = text.find('<a href=')
while m != -1:
    tag = text[m:m+200]
    if 'drawer-item' in tag or 'nav-item' in tag:
        line_no = text[:m].count('\n') + 1
        print(f'Line {line_no}: {tag[:120]}')
    m = text.find('<a href=', m+1)
