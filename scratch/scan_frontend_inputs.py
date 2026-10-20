from html.parser import HTMLParser
import os

class FormInputAuditor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = []
        self.textareas = []
        self.selects = []

    def handle_starttag(self, tag, attrs):
        attr_dict = {k.lower(): v for k, v in attrs}
        if tag == 'input':
            self.inputs.append(attr_dict)
        elif tag == 'textarea':
            self.textareas.append(attr_dict)
        elif tag == 'select':
            self.selects.append(attr_dict)

def audit_file(filepath, label):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    parser = FormInputAuditor()
    parser.feed(content)

    print(f"\n{'='*25} {label} {'='*25}")
    print(f"Total <input> elements: {len(parser.inputs)}")
    print(f"Total <textarea> elements: {len(parser.textareas)}")
    print(f"Total <select> elements: {len(parser.selects)}")

    unbounded_inputs = []
    for inp in parser.inputs:
        itype = inp.get('type', 'text').lower()
        if itype in ('hidden', 'submit', 'button', 'checkbox', 'radio', 'color'):
            continue
        ident = inp.get('id') or inp.get('name') or inp.get('placeholder') or str(inp)[:40]
        if itype == 'file':
            if not inp.get('accept'):
                unbounded_inputs.append(('file', ident, 'Missing accept filter'))
            continue
        if itype in ('number', 'range'):
            if 'max' not in inp or 'min' not in inp:
                unbounded_inputs.append((itype, ident, f"min={inp.get('min')} max={inp.get('max')}"))
            continue
        if itype in ('date', 'datetime-local', 'time'):
            if 'max' not in inp or 'min' not in inp:
                unbounded_inputs.append((itype, ident, f"min={inp.get('min')} max={inp.get('max')}"))
            continue
        # text / email / tel / password / search / url
        if 'maxlength' not in inp and 'readonly' not in inp and 'disabled' not in inp:
            unbounded_inputs.append((itype, ident, 'Missing maxlength'))

    print(f"Unbounded inputs found: {len(unbounded_inputs)}")
    for kind, ident, issue in unbounded_inputs:
        print(f"  [{kind}] {ident} -> {issue}")

    unbounded_textareas = []
    for ta in parser.textareas:
        ident = ta.get('id') or ta.get('name') or ta.get('placeholder') or str(ta)[:40]
        if 'maxlength' not in ta and 'readonly' not in ta and 'disabled' not in ta:
            unbounded_textareas.append((ident, 'Missing maxlength'))
    print(f"Unbounded textareas found: {len(unbounded_textareas)}")
    for ident, issue in unbounded_textareas:
        print(f"  [textarea] {ident} -> {issue}")

audit_file("frontend/index.html", "CUSTOMER APP HTML")
audit_file("admin_app/index.html", "ADMIN APP HTML")
