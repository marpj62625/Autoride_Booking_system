import re

with open('customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

tags = re.findall(r'<(input|textarea)([^>]+)>', content, re.IGNORECASE)
print(f'Total input/textarea tags found: {len(tags)}')
for tag, attrs in tags:
    t_match = re.search(r'type=["\']([^"\']+)["\']', attrs, re.I)
    id_match = re.search(r'id=["\']([^"\']+)["\']', attrs, re.I)
    name_match = re.search(r'name=["\']([^"\']+)["\']', attrs, re.I)
    max_match = re.search(r'maxlength=["\']([^"\']+)["\']', attrs, re.I)
    
    t = t_match.group(1).lower() if t_match else ('text' if tag.lower() == 'input' else 'textarea')
    eid = id_match.group(1) if id_match else (name_match.group(1) if name_match else 'NO_ID')
    maxl = max_match.group(1) if max_match else 'NONE'
    
    if t not in ['hidden', 'file', 'checkbox', 'radio', 'button', 'submit']:
        print(f'{tag:<8} id={eid:<28} type={t:<10} maxl={maxl}')

with open('customer_mobile/www/js/app.js', 'r', encoding='utf-8') as f:
    js_lines = f.readlines()

for idx, line in enumerate(js_lines, 1):
    for term in ['bfDestination', 'bfDeliveryAddress', 'refundAcctName', 'refundAcctNum', 'refundNotes', 'reviewComment', 'chatInput', 'lcInput', 'extRef', 'nlEmail', 'newProvider', 'inspNotes']:
        if term in line and ('<input' in line or '<textarea' in line):
            print(f'{idx}: {line.strip()[:110]}')


js_content = ''.join(js_lines)
js_tags = re.findall(r'<(input|textarea)([^>]+)>', js_content, re.IGNORECASE)

print(f'\nTotal input/textarea tags found in JS: {len(js_tags)}')
for tag, attrs in js_tags:
    t_match = re.search(r'type=["\']([^"\']+)["\']', attrs, re.I)
    id_match = re.search(r'id=["\']([^"\']+)["\']', attrs, re.I)
    name_match = re.search(r'name=["\']([^"\']+)["\']', attrs, re.I)
    max_match = re.search(r'maxlength=["\']([^"\']+)["\']', attrs, re.I)
    
    t = t_match.group(1).lower() if t_match else ('text' if tag.lower() == 'input' else 'textarea')
    eid = id_match.group(1) if id_match else (name_match.group(1) if name_match else 'NO_ID')
    maxl = max_match.group(1) if max_match else 'NONE'
    
    if t not in ['hidden', 'file', 'checkbox', 'radio', 'button', 'submit']:
        print(f'{tag:<8} id={eid:<28} type={t:<10} maxl={maxl}')

