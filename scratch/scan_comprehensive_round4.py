import os
import re

print("=== ROUND 4 COMPREHENSIVE SCAN ===")

# 1. Database schema check - let's check table schemas from backend/app.py or SQL files
backend_path = "backend/app.py"
with open(backend_path, "r", encoding="utf-8") as f:
    backend_content = f.read()

# Find all routes in backend/app.py
routes = re.findall(r"@app\.route\((['\"][^'\"]+['\"])[\s\S]*?def\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\):", backend_content)
print(f"Total endpoints defined: {len(routes)}")

# Find all direct int() or float() casts that might fail if malformed
int_casts = re.finditer(r"(int|float)\((request\.(?:form|args|json|values)\[[^\]]+\]|data(?:\[[^\]]+\]|\.get\([^)]+\)))\)", backend_content)
print("\n--- Direct Unsafe Typecasts ---")
for m in int_casts:
    start = max(0, m.start() - 50)
    end = min(len(backend_content), m.end() + 50)
    line_no = backend_content[:m.start()].count('\n') + 1
    # Check if inside a try block
    preceding = backend_content[max(0, m.start()-300):m.start()]
    if "try:" not in preceding:
        print(f"Line {line_no}: {m.group(0)}")

# Find all status updates without whitelist
print("\n--- Status updates check ---")
status_matches = re.finditer(r"status\s*=\s*(?:data|request\.json|request\.form)\.get\(['\"](?:status|booking_status|payment_status)['\"]", backend_content)
for m in status_matches:
    line_no = backend_content[:m.start()].count('\n') + 1
    snippet = backend_content[m.start():min(len(backend_content), m.start()+400)]
    # check if 'in [' or 'not in' or 'if status ==' in snippet
    if not any(k in snippet for k in ['in [', 'in (', 'not in', '== ']):
        # extract function name
        fn_match = re.search(r"def\s+([a-zA-Z0-9_]+)", backend_content[max(0, m.start()-1000):m.start()])
        fn_name = fn_match.group(1) if fn_match else "unknown"
        print(f"Line {line_no} in {fn_name}: status assigned without apparent whitelist check")

# Check frontend dynamic and static inputs in customer_mobile and admin_app
print("\n--- Checking Frontend inputs missing maxlength/bounds ---")
# Customer inputs
customer_html_path = "customer_mobile/www/index.html"
with open(customer_html_path, "r", encoding="utf-8") as f:
    cust_html = f.read()

cust_inputs = re.findall(r"<input\s+([^>]+)>", cust_html, re.IGNORECASE)
cust_missing = []
for inp in cust_inputs:
    if 'type="hidden"' in inp or 'type="checkbox"' in inp or 'type="radio"' in inp or 'type="file"' in inp or 'type="submit"' in inp or 'type="button"' in inp:
        continue
    if 'maxlength' not in inp and 'max=' not in inp:
        id_m = re.search(r'id=["\']([^"\']+)["\']', inp)
        name_m = re.search(r'name=["\']([^"\']+)["\']', inp)
        cust_missing.append(id_m.group(1) if id_m else (name_m.group(1) if name_m else inp[:40]))

print(f"Customer HTML inputs missing maxlength/max: {len(cust_missing)}")
if cust_missing:
    print(cust_missing[:20])

# Admin inputs
admin_html_path = "admin_app/index.html"
with open(admin_html_path, "r", encoding="utf-8") as f:
    admin_html = f.read()

admin_inputs = re.findall(r"<input\s+([^>]+)>", admin_html, re.IGNORECASE)
admin_missing = []
for inp in admin_inputs:
    if 'type="hidden"' in inp or 'type="checkbox"' in inp or 'type="radio"' in inp or 'type="file"' in inp or 'type="submit"' in inp or 'type="button"' in inp:
        continue
    if 'maxlength' not in inp and 'max=' not in inp:
        id_m = re.search(r'id=["\']([^"\']+)["\']', inp)
        name_m = re.search(r'name=["\']([^"\']+)["\']', inp)
        admin_missing.append(id_m.group(1) if id_m else (name_m.group(1) if name_m else inp[:40]))

print(f"Admin HTML inputs missing maxlength/max: {len(admin_missing)}")
if admin_missing:
    print(admin_missing[:20])
