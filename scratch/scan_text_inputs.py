import re

for fname in ["admin_app/index.html", "customer_mobile/www/index.html"]:
    with open(fname, "r", encoding="utf-8") as f:
        html = f.read()
    
    inps = re.findall(r'<input\s+([^>]+)>', html)
    print(f"\n--- Checking all text/email/search inputs in {fname} ---")
    missing_len = []
    for inp in inps:
        if any(f'type="{t}"' in inp for t in ['text', 'email', 'search', 'password', 'tel', 'url']):
            if 'maxlength=' not in inp:
                id_m = re.search(r'id=["\']([^"\']+)["\']', inp)
                missing_len.append(id_m.group(1) if id_m else inp[:40])
    print(f"Inputs missing maxlength: {len(missing_len)}")
    if missing_len:
        print(missing_len)
