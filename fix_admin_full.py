import re

with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

# ============================================================
# 1. REPLACE ALL INDIGO/BLUE/PURPLE WITH GRAB GREEN EQUIVALENTS
# ============================================================

# Primary indigo (#6366f1) -> Grab Green (#00B14F)
content = content.replace('#6366f1', '#00B14F')

# Dark indigo (#4f46e5) -> Grab Dark Green (#005339)
content = content.replace('#4f46e5', '#005339')

# Light indigo (#818cf8) -> Grab Green (#00B14F)
content = content.replace('#818cf8', '#00B14F')

# Blue (#3b82f6) -> Grab Green (#00B14F)
content = content.replace('#3b82f6', '#00B14F')

# Purple (#8b5cf6) -> Grab Teal (#5FDBE2)
content = content.replace('#8b5cf6', '#5FDBE2')

# Old green (#10b981) -> Grab Green (#00B14F)
content = content.replace('#10b981', '#00B14F')

# Old green rgba(16,185,129,...) -> rgba(0,177,79,...)
content = content.replace('rgba(16,185,129,', 'rgba(0,177,79,')

# Old indigo rgba(99,102,241,...) -> rgba(0,177,79,...)
content = content.replace('rgba(99,102,241,', 'rgba(0,177,79,')

# Fix darker green #059669 -> #005339
content = content.replace('#059669', '#005339')

with open('admin_mobile/www/index.html', 'w', encoding='latin-1') as f:
    f.write(content)

print('Done! Replaced all hardcoded colors.')

# Count remaining non-theme colors
hexes = re.findall(r'#[0-9a-fA-F]{6}\b', content)
from collections import Counter
c = Counter(hexes)
print('Remaining colors:')
for color, count in c.most_common(20):
    print(f'  {color}: {count}')
