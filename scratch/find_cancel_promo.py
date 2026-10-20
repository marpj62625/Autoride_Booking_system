import re

with open("backend/app.py", "r", encoding="utf-8") as f:
    backend_code = f.read()

# Check cancel and promo endpoints
for kw in ["cancel", "promo", "voucher", "discount"]:
    matches = re.finditer(rf"@app\.route\(['\"]([^'\"]*{kw}[^'\"]*)['\"].*methods=\[([^\]]+)\]", backend_code, re.IGNORECASE)
    print(f"\n--- Endpoints matching '{kw}' ---")
    for m in matches:
        line_no = backend_code[:m.start()].count('\n') + 1
        print(f"Line {line_no}: {m.group(1)} [{m.group(2)}]")
