with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'<button[^>]*bk-chip[^>]*>.*?</button>', text, re.IGNORECASE)
for m in matches:
    print(m)

# Also check how Bookings handles 'active' or 'picked_up' or 'completed'
pos = text.find('setFilter:')
if pos != -1:
    print(text[pos:pos+500])
else:
    pos2 = text.find('setFilter')
    if pos2 != -1:
        print(text[pos2:pos2+500])
