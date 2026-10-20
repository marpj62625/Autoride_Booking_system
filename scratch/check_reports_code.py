with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
pos = text.find('id="reports"')
if pos != -1:
    print("Found id='reports' at", pos)
    print(text[pos:pos+2500])
else:
    print("Not found id='reports'")

# Look for Reports object or function
pos2 = text.find('const Reports')
if pos2 == -1:
    pos2 = text.find('var Reports')
if pos2 == -1:
    pos2 = text.find('Reports =')
print("Reports JS object at:", pos2)
if pos2 != -1:
    print(text[pos2:pos2+2000])
