import re

def scan_js_dynamic_inputs(filepath, label):
    print(f"\n==================== SCANNING DYNAMIC JS INPUTS: {label} ({filepath}) ====================")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all occurrences of <input ...> in js strings or template literals
    input_matches = re.findall(r'<input\b[^>]*>', content, re.IGNORECASE)
    print(f"Total dynamic <input> strings found: {len(input_matches)}")
    
    missing_limits = []
    for m in input_matches:
        # Check type
        t_m = re.search(r'type=[\'"]([^\'"]+)[\'"]', m, re.IGNORECASE)
        itype = t_m.group(1).lower() if t_m else 'text'
        id_m = re.search(r'id=[\'"]([^\'"]+)[\'"]', m, re.IGNORECASE)
        iid = id_m.group(1) if id_m else 'NO_ID'
        
        if itype == 'number':
            if 'min=' not in m or 'max=' not in m:
                missing_limits.append(('NUMBER_NO_BOUND', iid, itype, m))
        elif itype in ('text', 'search', 'email', 'password', 'tel', 'url'):
            if 'maxlength=' not in m and 'readonly' not in m and 'disabled' not in m:
                missing_limits.append(('TEXT_NO_MAXLENGTH', iid, itype, m))
        elif itype == 'file':
            if 'accept=' not in m:
                missing_limits.append(('FILE_NO_ACCEPT', iid, itype, m))

    print(f"Found {len(missing_limits)} dynamic inputs missing limits:")
    for kind, iid, itype, tag in missing_limits:
        print(f"  [{kind}] id='{iid}' type='{itype}': {tag[:120]}")

    # Check textareas
    ta_matches = re.findall(r'<textarea\b[^>]*>', content, re.IGNORECASE)
    print(f"Total dynamic <textarea> strings found: {len(ta_matches)}")
    for m in ta_matches:
        if 'maxlength=' not in m and 'readonly' not in m and 'disabled' not in m:
            id_m = re.search(r'id=[\'"]([^\'"]+)[\'"]', m, re.IGNORECASE)
            iid = id_m.group(1) if id_m else 'NO_ID'
            print(f"  [TEXTAREA_NO_MAXLENGTH] id='{iid}': {m[:120]}")

scan_js_dynamic_inputs('AutorideSystem/customer_mobile/www/js/app.js', 'CUSTOMER JS')
scan_js_dynamic_inputs('AutorideSystem/customer_mobile/www/js/utils.js', 'CUSTOMER UTILS')
scan_js_dynamic_inputs('AutorideSystem/admin_app/index.html', 'ADMIN INLINE JS')
