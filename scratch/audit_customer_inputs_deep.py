import re
from html.parser import HTMLParser

class InputScanner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = []
        
    def handle_starttag(self, tag, attrs):
        if tag in ['input', 'textarea', 'select']:
            attr_dict = dict(attrs)
            self.inputs.append((tag, attr_dict))

with open('customer_mobile/www/index.html', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

parser = InputScanner()
parser.feed(content)

print(f"Total form elements found in customer_mobile/www/index.html: {len(parser.inputs)}")

missing = []
for tag, attrs in parser.inputs:
    el_id = attrs.get('id', '')
    el_type = attrs.get('type', 'text' if tag == 'input' else tag)
    maxlength = attrs.get('maxlength')
    min_val = attrs.get('min')
    max_val = attrs.get('max')
    
    # Exclude buttons, submit, checkbox, radio, hidden, file
    if el_type in ['button', 'submit', 'checkbox', 'radio', 'hidden', 'file', 'date', 'time']:
        continue
        
    if el_type in ['text', 'email', 'tel', 'password', 'search', 'textarea']:
        if not maxlength:
            missing.append((el_id, el_type, tag, attrs.get('placeholder', '')))
    elif el_type == 'number':
        if not max_val:
            missing.append((el_id, el_type, tag, f"min={min_val} max={max_val}"))

print(f"\nInputs missing maxlength or max bound: {len(missing)}")
for el_id, el_type, tag, extra in missing:
    print(f"  ID: {el_id:<28} Type: {el_type:<10} Tag: {tag:<8} Extra: {extra}")
