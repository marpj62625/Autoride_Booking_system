import re

def audit_js_file(filepath, label):
    with open(filepath, 'r', encoding='utf-8') as f:
        js = f.read()

    print(f"\n{'='*25} {label} {'='*25}")
    # Find all occurrences of <input ...> in js
    inputs = re.findall(r'<input\s+[^>]+>', js, re.IGNORECASE)
    print(f"Total dynamic <input> templates found: {len(inputs)}")

    unbounded = []
    for inp in inputs:
        itype = 'text'
        m_type = re.search(r'type=["\']([^"\']+)["\']', inp, re.IGNORECASE)
        if m_type:
            itype = m_type.group(1).lower()

        if itype in ('hidden', 'submit', 'button', 'checkbox', 'radio', 'color'):
            continue

        if itype == 'file':
            if 'accept=' not in inp.lower():
                unbounded.append(('file', inp[:70], 'Missing accept'))
            continue

        if itype in ('number', 'range'):
            if 'max=' not in inp.lower() or 'min=' not in inp.lower():
                unbounded.append((itype, inp[:70], 'Missing min/max'))
            continue

        if itype in ('date', 'datetime-local', 'time'):
            if 'max=' not in inp.lower() or 'min=' not in inp.lower():
                unbounded.append((itype, inp[:70], 'Missing min/max'))
            continue

        # Textual
        if 'maxlength=' not in inp.lower() and 'readonly' not in inp.lower() and 'disabled' not in inp.lower():
            unbounded.append((itype, inp[:70], 'Missing maxlength'))

    print(f"Unbounded dynamic inputs: {len(unbounded)}")
    for kind, snippet, issue in unbounded:
        print(f"  [{kind}] {snippet} -> {issue}")

    # Check textareas
    textareas = re.findall(r'<textarea\s+[^>]*>', js, re.IGNORECASE)
    print(f"Total dynamic <textarea> templates found: {len(textareas)}")
    unbounded_tas = []
    for ta in textareas:
        if 'maxlength=' not in ta.lower() and 'readonly' not in ta.lower() and 'disabled' not in ta.lower():
            unbounded_tas.append((ta[:70], 'Missing maxlength'))
    print(f"Unbounded dynamic textareas: {len(unbounded_tas)}")
    for snippet, issue in unbounded_tas:
        print(f"  [textarea] {snippet} -> {issue}")

audit_js_file("frontend/js/app.js", "CUSTOMER APP JS")
audit_js_file("admin_app/js/app.js", "ADMIN APP JS")
