with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

for tab_id in ['chat', 'reports', 'vehicles', 'bookings', 'activity', 'staff']:
    m = re.search(r'id=["\']' + tab_id + r'["\']', text)
    if m:
        lines = text[:m.start()].splitlines()
        print(f"Tab '{tab_id}' at line {len(lines)+1}")
        print("  " + text[m.start():m.start()+250].replace('\n', ' '))
