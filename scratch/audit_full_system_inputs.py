import re
import os

def analyze_html_or_js(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Find all input, textarea, select tags
    tags = re.findall(r'<(input|textarea|select)([^>]*)(?:>|/>)', content, re.IGNORECASE)
    results = []
    
    for tag_name, attrs in tags:
        tag_name = tag_name.lower()
        t_match = re.search(r'type=["\']([^"\']+)["\']', attrs, re.I)
        id_match = re.search(r'id=["\']([^"\']+)["\']', attrs, re.I)
        name_match = re.search(r'name=["\']([^"\']+)["\']', attrs, re.I)
        maxl_match = re.search(r'maxlength=["\']([^"\']+)["\']', attrs, re.I)
        min_match = re.search(r'min=["\']([^"\']+)["\']', attrs, re.I)
        max_match = re.search(r'max=["\']([^"\']+)["\']', attrs, re.I)
        placeholder_match = re.search(r'placeholder=["\']([^"\']+)["\']', attrs, re.I)
        oninput_match = re.search(r'oninput=["\']([^"\']+)["\']', attrs, re.I)
        
        t = t_match.group(1).lower() if t_match else ('text' if tag_name == 'input' else tag_name)
        eid = id_match.group(1) if id_match else (name_match.group(1) if name_match else '')
        maxl = maxl_match.group(1) if maxl_match else None
        min_val = min_match.group(1) if min_match else None
        max_val = max_match.group(1) if max_match else None
        placeholder = placeholder_match.group(1) if placeholder_match else ''
        oninput = oninput_match.group(1) if oninput_match else ''
        
        # We care about user-enterable fields (skip hidden, submit, button, checkbox, radio for text limits, though keep number/file/date for boundary limits)
        results.append({
            'file': filepath,
            'tag': tag_name,
            'type': t,
            'id': eid,
            'maxlength': maxl,
            'min': min_val,
            'max': max_val,
            'placeholder': placeholder,
            'oninput': oninput,
            'raw_attrs': attrs.strip()
        })
    return results

print('Scanning Customer App...')
customer_html = analyze_html_or_js('customer_mobile/www/index.html')
customer_js = analyze_html_or_js('customer_mobile/www/js/app.js')

print(f'Customer HTML: {len(customer_html)} tags')
print(f'Customer JS: {len(customer_js)} tags')

print('Scanning Admin App...')
admin_html = analyze_html_or_js('admin_app/index.html')
admin_bm_js = analyze_html_or_js('admin_app/booking-management.js')
admin_vm_js = analyze_html_or_js('admin_app/vehicle-management.js')
admin_rep_js = analyze_html_or_js('admin_app/reports.js')

print(f'Admin HTML: {len(admin_html)} tags')
print(f'Admin Booking Mgmt JS: {len(admin_bm_js)} tags')
print(f'Admin Vehicle Mgmt JS: {len(admin_vm_js)} tags')
print(f'Admin Reports JS: {len(admin_rep_js)} tags')

all_admin = admin_html + admin_bm_js + admin_vm_js + admin_rep_js
all_customer = customer_html + customer_js

# Filter to enterable inputs
def filter_enterable(items):
    seen = set()
    res = []
    for item in items:
        # Ignore buttons and hidden unless specific
        if item['type'] in ['button', 'submit', 'image', 'reset']:
            continue
        key = (item['file'], item['id'], item['type'])
        if key in seen and item['id']:
            continue
        seen.add(key)
        res.append(item)
    return res

ent_customer = filter_enterable(all_customer)
ent_admin = filter_enterable(all_admin)

print(f'\nEnterable Customer Fields: {len(ent_customer)}')
print(f'Enterable Admin Fields: {len(ent_admin)}')

with open('scratch/all_fields_dump.txt', 'w', encoding='utf-8') as out:
    out.write('=== CUSTOMER FIELDS ===\n')
    for item in ent_customer:
        out.write(f"[{item['type']:<10}] ID: {item['id']:<26} MAXL: {str(item['maxlength']):<6} MIN: {str(item['min']):<10} MAX: {str(item['max']):<10} PH: {item['placeholder'][:30]}\n")
    out.write('\n=== ADMIN FIELDS ===\n')
    for item in ent_admin:
        out.write(f"[{item['type']:<10}] ID: {item['id']:<26} MAXL: {str(item['maxlength']):<6} MIN: {str(item['min']):<10} MAX: {str(item['max']):<10} PH: {item['placeholder'][:30]}\n")

print('Dumped to scratch/all_fields_dump.txt')
