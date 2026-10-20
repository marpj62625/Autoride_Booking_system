import re

for fname in ["customer_mobile/www/index.html", "customer_mobile/www/js/app.js"]:
    with open(fname, "r", encoding="utf-8") as f:
        content = f.read()
    
    matches = re.finditer(r'<input\s+([^>]+)>', content)
    unbounded = []
    for m in matches:
        tag = m.group(0)
        if any(f'type="{t}"' in tag for t in ['submit', 'button', 'checkbox', 'radio', 'hidden', 'file', 'color']):
            continue
        if 'maxlength' not in tag and 'max=' not in tag:
            line_no = content[:m.start()].count('\n') + 1
            unbounded.append((line_no, tag[:80]))
    print(f"\n{fname}: Total unbounded inputs: {len(unbounded)}")
    for lno, snip in unbounded:
        print(f"  Line {lno}: {snip}")
