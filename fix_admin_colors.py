import re

with open('admin_mobile/www/index.html', 'r', encoding='latin-1') as f:
    content = f.read()

# Replace CSS variables
content = content.replace('--primary: #0052ff;', '--primary: #00B14F;')
content = content.replace('--primary-dark: #0040CC;', '--primary-dark: #005339;')
content = content.replace('--primary-light: #4D8FFF;', '--primary-light: #7bdcb5;')

# Dark mode variables
content = content.replace('--primary: #4D8FFF;', '--primary: #00B14F;')
content = content.replace('--primary-dark: #0052FF;', '--primary-dark: #00B14F;')
content = content.replace('--primary-light: #80AFFF;', '--primary-light: #005339;')

# Search for any #0052ff gradients in the HTML
content = content.replace('linear-gradient(160deg,#0052ff 0%,#0040CC 60%,#001a66 100%)', 'linear-gradient(160deg,var(--primary-light) 0%,var(--primary) 60%,var(--primary-dark) 100%)')
content = content.replace('linear-gradient(160deg,#0052ff 0%,#0040CC 50%,#001a66 100%)', 'linear-gradient(160deg,var(--primary-light) 0%,var(--primary) 50%,var(--primary-dark) 100%)')
content = content.replace('linear-gradient(135deg,var(--primary),var(--primary-dark))', 'var(--primary)')

# Fix button colors (if there is hardcoded text color issue)
# e.g. color:var(--text-primary) on buttons
content = content.replace('background:var(--primary);color:var(--text-primary);', 'background:var(--primary);color:#ffffff;')
content = content.replace('background:var(--primary); color:var(--text-primary);', 'background:var(--primary); color:#ffffff;')
content = content.replace('background:var(--primary);color:#fff;', 'background:var(--primary);color:#ffffff;')

# Fix the pill CSS rules
pills_old = '''.pill-confirmed { background:#cfe2ff; color:#084298; }
.pill-approved { background:#d1e7dd; color:#0a3622; }
.pill-picked-up { background:#e2d9f3; color:#432874; }
.pill-completed { background:#d1e7dd; color:#0a3622; }
.pill-cancelled { background:#f8d7da; color:#842029; }
.pill-rejected { background:#f8d7da; color:#842029; }
.pill-unpaid { background:#f8d7da; color:#842029; }
.pill-partially-paid { background:#fff3cd; color:#856404; }
.pill-paid { background:#d1e7dd; color:#0a3622; }
.pill-refund-pending { background:#fff3cd; color:#856404; }
.pill-refunded { background:#cfe2ff; color:#084298; }'''

pills_new = '''.pill-confirmed { background:transparent; color:var(--primary); border:1px solid var(--primary); }
.pill-approved { background:transparent; color:var(--primary); border:1px solid var(--primary); }
.pill-picked-up { background:transparent; color:var(--primary); border:1px solid var(--primary); }
.pill-completed { background:transparent; color:var(--primary); border:1px solid var(--primary); }
.pill-cancelled { background:transparent; color:var(--danger); border:1px solid var(--danger); }
.pill-rejected { background:transparent; color:var(--danger); border:1px solid var(--danger); }
.pill-unpaid { background:transparent; color:var(--danger); border:1px solid var(--danger); }
.pill-partially-paid { background:transparent; color:var(--warning); border:1px solid var(--warning); }
.pill-paid { background:transparent; color:var(--primary); border:1px solid var(--primary); }
.pill-refund-pending { background:transparent; color:var(--warning); border:1px solid var(--warning); }
.pill-refunded { background:transparent; color:var(--primary); border:1px solid var(--primary); }'''

content = content.replace(pills_old, pills_new)

# Fix Javascript statusColors hardcoded inside JS
content = content.replace('#fbbf24', '#f59e0b')
content = content.replace('#34d399', '#00B14F') # Confirmed, Approved, Paid
content = content.replace('#a78bfa', '#00B14F') # Completed, Picked Up
# wait, if Javascript has statusColors = {'Confirmed': '#34d399', ...} this replaces it correctly.

with open('admin_mobile/www/index.html', 'w', encoding='latin-1') as f:
    f.write(content)

print("Admin colors updated")
