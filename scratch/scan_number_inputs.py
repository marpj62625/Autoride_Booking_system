import re

for fname in ["admin_app/index.html", "customer_mobile/www/index.html"]:
    with open(fname, "r", encoding="utf-8") as f:
        html = f.read()
    
    inps = re.findall(r'<input\s+([^>]+)>', html)
    print(f"\n--- Checking number inputs in {fname} ---")
    missing_max = []
    for inp in inps:
        if 'type="number"' in inp or 'inputmode="numeric"' in inp:
            if 'max=' not in inp and 'maxlength=' not in inp:
                id_m = re.search(r'id=["\']([^"\']+)["\']', inp)
                missing_max.append(id_m.group(1) if id_m else inp[:40])
    print(f"Number inputs missing max/maxlength: {len(missing_max)}")
    if missing_max:
        print(missing_max)
