import re
import json

def get_context(filepath, line_num, max_back=15):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    start = max(0, line_num - max_back)
    chunk = ''.join(lines[start:line_num])
    
    # Check for modals, headers, or section comments
    h_match = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', chunk, re.I)
    modal_match = re.findall(r'id=["\']([a-zA-Z0-9_-]*(?:modal|dialog|card|section|tab|page)[a-zA-Z0-9_-]*)["\']', chunk, re.I)
    legend_match = re.findall(r'<legend[^>]*>(.*?)</legend>', chunk, re.I)
    
    ctx = []
    if modal_match:
        ctx.append(modal_match[-1])
    if h_match:
        ctx.append(re.sub(r'<[^>]+>', '', h_match[-1]).strip())
    if legend_match:
        ctx.append(re.sub(r'<[^>]+>', '', legend_match[-1]).strip())
        
    return ' > '.join(ctx) if ctx else 'General'

def parse_detailed(filepath):
    results = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    full_text = ''.join(lines)
    # Match input, textarea, select
    pattern = re.compile(r'<(input|textarea|select)([^>]*)(?:>|/>)', re.IGNORECASE)
    
    for m in pattern.finditer(full_text):
        tag = m.group(1).lower()
        attrs = m.group(2)
        pos = m.start()
        line_num = full_text[:pos].count('\n') + 1
        
        t_match = re.search(r'type=["\']([^"\']+)["\']', attrs, re.I)
        id_match = re.search(r'id=["\']([^"\']+)["\']', attrs, re.I)
        name_match = re.search(r'name=["\']([^"\']+)["\']', attrs, re.I)
        maxl_match = re.search(r'maxlength=["\']([^"\']+)["\']', attrs, re.I)
        min_match = re.search(r'min=["\']([^"\']+)["\']', attrs, re.I)
        max_match = re.search(r'max=["\']([^"\']+)["\']', attrs, re.I)
        step_match = re.search(r'step=["\']([^"\']+)["\']', attrs, re.I)
        placeholder_match = re.search(r'placeholder=["\']([^"\']+)["\']', attrs, re.I)
        accept_match = re.search(r'accept=["\']([^"\']+)["\']', attrs, re.I)
        oninput_match = re.search(r'oninput=["\']([^"\']+)["\']', attrs, re.I)
        
        t = t_match.group(1).lower() if t_match else ('text' if tag == 'input' else tag)
        eid = id_match.group(1) if id_match else (name_match.group(1) if name_match else '')
        
        if t in ['button', 'submit', 'reset', 'image']:
            continue
            
        context = get_context(filepath, line_num)
        
        results.append({
            'file': filepath,
            'line': line_num,
            'tag': tag,
            'type': t,
            'id': eid,
            'maxlength': maxl_match.group(1) if maxl_match else None,
            'min': min_match.group(1) if min_match else None,
            'max': max_match.group(1) if max_match else None,
            'step': step_match.group(1) if step_match else None,
            'placeholder': placeholder_match.group(1) if placeholder_match else '',
            'accept': accept_match.group(1) if accept_match else '',
            'oninput': oninput_match.group(1) if oninput_match else '',
            'context': context
        })
    return results

customer_html_items = parse_detailed('customer_mobile/www/index.html')
customer_js_items = parse_detailed('customer_mobile/www/js/app.js')
admin_html_items = parse_detailed('admin_app/index.html')

all_data = {
    'customer_html': customer_html_items,
    'customer_js': customer_js_items,
    'admin_html': admin_html_items
}

with open('scratch/detailed_inputs_catalog.json', 'w', encoding='utf-8') as f:
    json.dump(all_data, f, indent=2)

print(f"Catalog saved: Customer HTML ({len(customer_html_items)}), Customer JS ({len(customer_js_items)}), Admin HTML ({len(admin_html_items)})")
