import re
import os

files_to_check = [
    "frontend/js/app.js",
    "frontend/index.html",
    "admin_app/index.html",
    "admin_app/booking-management.js",
    "admin_app/reports.js",
    "admin_app/shared-utils.js",
    "admin_app/vehicle-management.js",
]

total_dynamic_inputs = 0
total_dynamic_textareas = 0
all_unbounded = []

for filepath in files_to_check:
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # If html, extract script tags
    if filepath.endswith('.html'):
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL | re.IGNORECASE)
        code = "\n".join(scripts)
    else:
        code = content

    # Find template string inputs or string-concatenated inputs
    inputs = re.findall(r'<input\s+[^>]+>', code, re.IGNORECASE)
    total_dynamic_inputs += len(inputs)

    for inp in inputs:
        itype = 'text'
        m_type = re.search(r'type=["\']([^"\']+)["\']', inp, re.IGNORECASE)
        if m_type:
            itype = m_type.group(1).lower()

        if itype in ('hidden', 'submit', 'button', 'checkbox', 'radio', 'color'):
            continue

        if itype == 'file':
            if 'accept=' not in inp.lower():
                all_unbounded.append((filepath, itype, inp[:60], 'Missing accept attribute'))
            continue

        if itype in ('number', 'range'):
            if 'max=' not in inp.lower() or 'min=' not in inp.lower():
                all_unbounded.append((filepath, itype, inp[:60], 'Missing min or max'))
            continue

        if itype in ('date', 'datetime-local', 'time'):
            if 'max=' not in inp.lower() or 'min=' not in inp.lower():
                all_unbounded.append((filepath, itype, inp[:60], 'Missing min or max'))
            continue

        if 'maxlength=' not in inp.lower() and 'readonly' not in inp.lower() and 'disabled' not in inp.lower():
            all_unbounded.append((filepath, itype, inp[:60], 'Missing maxlength'))

    textareas = re.findall(r'<textarea\s+[^>]*>', code, re.IGNORECASE)
    total_dynamic_textareas += len(textareas)
    for ta in textareas:
        if 'maxlength=' not in ta.lower() and 'readonly' not in ta.lower() and 'disabled' not in ta.lower():
            all_unbounded.append((filepath, 'textarea', ta[:60], 'Missing maxlength'))

print(f"Total dynamic <input> detected in JS code: {total_dynamic_inputs}")
print(f"Total dynamic <textarea> detected in JS code: {total_dynamic_textareas}")
print(f"Unbounded dynamic elements: {len(all_unbounded)}")
for fp, kind, snippet, issue in all_unbounded:
    print(f"  [{fp}] [{kind}] {snippet} -> {issue}")
