import re

with open('customer_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

# 1. Fix btn-primary text color
content = content.replace(
    '.btn-primary { background:var(--primary); color:var(--text-primary);',
    '.btn-primary { background:var(--primary); color:var(--on-primary);'
)

# 2. Fix toggle-group active text color
content = content.replace(
    '.toggle-group button.active { background:var(--primary); color:var(--text-primary); }',
    '.toggle-group button.active { background:var(--primary); color:var(--on-primary); }'
)

# 3. Fix badge-avail-yes
content = content.replace(
    '.badge-avail-yes { background:rgba(5,150,105,0.85); color:var(--text-primary); }',
    '.badge-avail-yes { background:var(--primary); color:var(--on-primary); }'
)

# 4. Fix vehicle-rate text color to primary (like Grab's green price text in bookings, wait, the screenshot of browse shows black price text, but bookings shows green total. For now, let's leave vehicle-rate as is or make it primary if we want, currently it's red #dc2626)
content = content.replace(
    '.vehicle-rate { font-size:1.1rem; font-weight:900; color:#dc2626; }',
    '.vehicle-rate { font-size:1.1rem; font-weight:900; color:var(--text-primary); }'
)

# 5. Fix filter chips active color (if any)
# I need to check the JS or CSS for filter chips to see how active is styled.
# Let's save the file.
with open('customer_mobile/www/index.html', 'w', encoding='latin-1') as f:
    f.write(content)

print("Updated button and badge colors")
