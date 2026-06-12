import re

with open('customer_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

# 1. Fix .home-banner CSS text color
content = content.replace(
    '.home-banner { background:linear-gradient(135deg, var(--primary), var(--primary-dark)); color:var(--text-primary);',
    '.home-banner { background:linear-gradient(135deg, var(--primary), var(--primary-dark)); color:var(--on-primary);'
)

# 2. Fix 'Good day' text color
content = content.replace(
    'color:rgba(255,200,200,0.8);',
    'color:rgba(255,255,255,0.8);'
)

# 3. Fix homeUserName text color
content = content.replace(
    'color:var(--text-primary);margin-top:2px;letter-spacing:-0.5px;">there</h2>',
    'color:var(--on-primary);margin-top:2px;letter-spacing:-0.5px;">there</h2>'
)

# 4. Fix notification bell color
content = content.replace(
    'color:var(--text-primary);width:40px;height:40px;border-radius:14px;',
    'color:var(--on-primary);width:40px;height:40px;border-radius:14px;'
)

# 5. Fix Loyalty Points award icon color
content = content.replace(
    'class="fas fa-award" style="color:var(--text-primary);',
    'class="fas fa-award" style="color:#ffffff;'
)

# 6. Fix Loyalty Points number color
content = content.replace(
    'id="homePoints" style="font-size:1.6rem;font-weight:900;color:var(--text-primary);',
    'id="homePoints" style="font-size:1.6rem;font-weight:900;color:var(--on-primary);'
)

# 7. Replace Quick Action 1 (Red -> Green)
content = content.replace(
    'background:rgba(220,38,38,0.1);',
    'background:rgba(0,177,79,0.1);'
).replace(
    'background:linear-gradient(135deg,#dc2626,#9b1a1a);',
    'background:var(--primary);'
)

# 8. Replace Quick Action 2 (Blue -> Green)
content = content.replace(
    'background:rgba(37,99,235,0.1);',
    'background:rgba(0,177,79,0.1);'
).replace(
    'background:linear-gradient(135deg,#2563eb,#1d4ed8);',
    'background:var(--primary);'
)

# 9. Replace Quick Action 3 (Dark Teal -> Green)
content = content.replace(
    'background:rgba(5,150,105,0.1);',
    'background:rgba(0,177,79,0.1);'
).replace(
    'background:linear-gradient(135deg,#059669,#047857);',
    'background:var(--primary);'
)

# 10. Replace Quick Action 4 (Purple -> Green)
content = content.replace(
    'background:rgba(124,58,237,0.1);',
    'background:rgba(0,177,79,0.1);'
).replace(
    'background:linear-gradient(135deg,#7c3aed,#6d28d9);',
    'background:var(--primary);'
)

# 11. Fix Quick Action icon colors (var(--text-primary) -> var(--on-primary))
# Only inside the quick actions block.
def replace_qa_icons(match):
    return match.group(0).replace('var(--text-primary)', 'var(--on-primary)')

content = re.sub(r'<div style="display:grid;grid-template-columns:repeat\(4,1fr\);gap:8px;">.*?</div>\s+</div>', replace_qa_icons, content, flags=re.DOTALL)

with open('customer_mobile/www/index.html', 'w', encoding='latin-1') as f:
    f.write(content)

print("Updated index.html successfully")
