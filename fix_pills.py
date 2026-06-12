import re

with open('customer_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

# Grab-style pills
content = content.replace(
    '.pill-confirmed { background:#cfe2ff; color:#084298; }',
    '.pill-confirmed { background:var(--primary); color:var(--on-primary); }'
).replace(
    '.pill-paid { background:#d1e7dd; color:#0a3622; }',
    '.pill-paid { background:var(--primary); color:var(--on-primary); }'
).replace(
    '.pill-approved { background:#d1e7dd; color:#0a3622; }',
    '.pill-approved { background:var(--primary); color:var(--on-primary); }'
).replace(
    '.pill-completed { background:#d1e7dd; color:#0a3622; }',
    '.pill-completed { background:var(--primary); color:var(--on-primary); }'
).replace(
    '.pill-picked-up { background:#e2d9f3; color:#432874; }',
    '.pill-picked-up { background:var(--primary); color:var(--on-primary); }'
)

# And also let's change the price text in the Bookings card (if there is one).
# We fixed vehicle-rate earlier in fix_buttons.py (wait I didn't actually do it).

with open('customer_mobile/www/index.html', 'w', encoding='latin-1') as f:
    f.write(content)

with open('customer_mobile/www/js/app.js', 'r', encoding='latin-1') as f:
    js = f.read()

# Check for hardcoded PHP prices in renderBookingsList
# It usually looks like style="color:#0a3622;" or something. We will just use regex to replace price colors.
js = re.sub(r'color:#(?:10b981|059669|16a34a|0a3622|34d399);', r'color:var(--primary);', js)
js = re.sub(r'color: #(?:10b981|059669|16a34a|0a3622|34d399);', r'color:var(--primary);', js)

with open('customer_mobile/www/js/app.js', 'w', encoding='latin-1') as f:
    f.write(js)

print("Updated pills and prices to Grab Green")
