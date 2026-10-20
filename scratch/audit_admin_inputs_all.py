import re

with open("admin_app/index.html", "r", encoding="utf-8") as f:
    admin_html = f.read()

# Find all <input in javascript strings
matches = re.finditer(r'<input\s+([^>]+)>', admin_html)
print(f"Total <input> in admin_app/index.html: {len(list(matches))}")

matches = re.finditer(r'<input\s+([^>]+)>', admin_html)
unbounded = []
for m in matches:
    tag = m.group(0)
    # ignore buttons, checkboxes, radio, hidden, file, color
    if any(f'type="{t}"' in tag for t in ['submit', 'button', 'checkbox', 'radio', 'hidden', 'file', 'color']):
        continue
    if 'maxlength' not in tag and 'max=' not in tag:
        line_no = admin_html[:m.start()].count('\n') + 1
        unbounded.append((line_no, tag[:80]))

print(f"Unbounded inputs in admin_app/index.html: {len(unbounded)}")
for lno, snip in unbounded:
    print(f"Line {lno}: {snip}")
