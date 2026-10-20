from html.parser import HTMLParser

class AdminInputScanner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = []
        
    def handle_starttag(self, tag, attrs):
        if tag in ['input', 'textarea', 'select']:
            attr_dict = dict(attrs)
            self.inputs.append((tag, attr_dict))

with open('admin_app/index.html', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

parser = AdminInputScanner()
parser.feed(content)

missing_number_bounds = []
missing_text_maxlength = []

for tag, attrs in parser.inputs:
    el_id = attrs.get('id', '')
    el_type = attrs.get('type', 'text' if tag == 'input' else tag)
    maxlength = attrs.get('maxlength')
    min_val = attrs.get('min')
    max_val = attrs.get('max')
    
    if el_type in ['button', 'submit', 'checkbox', 'radio', 'hidden', 'file', 'date', 'time']:
        continue
        
    if el_type == 'number':
        if not min_val or not max_val:
            missing_number_bounds.append((el_id, attrs.get('placeholder', ''), f"min={min_val} max={max_val}"))
    elif el_type in ['text', 'email', 'password', 'tel', 'search', 'textarea']:
        if not maxlength:
            missing_text_maxlength.append((el_id, el_type, tag, attrs.get('placeholder', '')))

with open('scratch/admin_missing_limits_report.txt', 'w', encoding='utf-8') as out:
    out.write(f"Total form elements: {len(parser.inputs)}\n")
    out.write(f"\n[NUMBER INPUTS MISSING MIN/MAX]: {len(missing_number_bounds)}\n")
    for el_id, ph, bounds in missing_number_bounds:
        out.write(f"  ID: {el_id:<28} Bounds: {bounds:<20} PH: {ph}\n")

    out.write(f"\n[TEXT/TEXTAREA MISSING MAXLENGTH]: {len(missing_text_maxlength)}\n")
    for el_id, el_type, tag, ph in missing_text_maxlength:
        out.write(f"  ID: {el_id:<28} Type: {el_type:<10} Tag: {tag:<8} PH: {ph}\n")

print(f"Report written to scratch/admin_missing_limits_report.txt! Numbers: {len(missing_number_bounds)}, Text: {len(missing_text_maxlength)}")
