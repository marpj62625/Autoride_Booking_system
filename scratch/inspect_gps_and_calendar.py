with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Find GPS tab
m_gps = re.search(r'id=["\']gps["\']', text)
if m_gps:
    print("Found GPS tab at char:", m_gps.start())
    lines = text[:m_gps.start()].splitlines()
    print("Line:", len(lines)+1)
    print(text[m_gps.start()-100:m_gps.start()+500])

# Find fleet-calendar container and its CSS
m_fc = re.search(r'id=["\']fleet-calendar["\']', text)
if m_fc:
    print("\nFound fleet-calendar at char:", m_fc.start())
    lines = text[:m_fc.start()].splitlines()
    print("Line:", len(lines)+1)
    print(text[m_fc.start()-100:m_fc.start()+500])
