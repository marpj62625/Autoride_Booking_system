import ast
import os
import re

print("=== ROUND 5 DEEP SCAN ===")

backend_path = "backend/app.py"
with open(backend_path, "r", encoding="utf-8") as f:
    backend_code = f.read()

lines = backend_code.split('\n')

# 1. SCAN ALL `int(` and `float(` calls in backend/app.py
print("\n--- 1. Scanning for Unprotected int()/float() Typecasts ---")
unsafe_casts = []
for idx, line in enumerate(lines):
    # Match int(x) or float(x) where x comes from request or data
    m = re.search(r"(int|float)\(((?:request\.(?:args|form|json|values)|data)\.get\(['\"][a-zA-Z0-9_]+['\"][^)]*\))", line)
    if not m:
        m = re.search(r"(int|float)\(((?:request\.(?:args|form|json|values)|data)\[['\"][a-zA-Z0-9_]+['\"]\])", line)
    if m:
        # Check if inside a try block within the preceding 20 lines
        preceding = "\n".join(lines[max(0, idx-20):idx])
        if "try:" not in preceding:
            unsafe_casts.append((idx + 1, line.strip(), m.group(0)))

print(f"Total unprotected typecasts found: {len(unsafe_casts)}")
for lno, ltext, mtext in unsafe_casts[:15]:
    print(f"Line {lno}: {mtext} in `{ltext[:70]}`")

# 2. SCAN FOR UNBOUNDED TEXTAREAS IN FRONTEND & ADMIN
print("\n--- 2. Scanning Textareas for Missing maxlength ---")
files_to_check = [
    ("admin_app/index.html", "Admin HTML"),
    ("customer_mobile/www/index.html", "Customer HTML"),
    ("customer_mobile/www/js/app.js", "Customer JS")
]

missing_textareas = []
for fpath, label in files_to_check:
    if not os.path.exists(fpath): continue
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    # find all <textarea
    tas = re.findall(r'<textarea\s+([^>]+)>', content, re.IGNORECASE)
    for ta in tas:
        if 'maxlength' not in ta.lower():
            id_m = re.search(r'id=["\']([^"\']+)["\']', ta)
            name_m = re.search(r'name=["\']([^"\']+)["\']', ta)
            identifier = id_m.group(1) if id_m else (name_m.group(1) if name_m else ta[:30])
            missing_textareas.append((label, identifier, ta[:60]))

print(f"Total textareas missing maxlength: {len(missing_textareas)}")
for lbl, ident, snippet in missing_textareas:
    print(f"  [{lbl}] {ident}: `{snippet}`")

# 3. SCAN FOR UNSANITIZED SQL PARAMETERS OR DIRECT INJECTIONS
print("\n--- 3. Scanning for String Formatting in SQL Queries ---")
sql_fstrings = []
for idx, line in enumerate(lines):
    if ("execute(f\"" in line or "execute(f'" in line or "execute(\"" in line or "execute('" in line) and "%s" not in line:
        if "{" in line and "}" in line and "execute(" in line:
            sql_fstrings.append((idx+1, line.strip()))

print(f"Potential SQL f-strings: {len(sql_fstrings)}")
for lno, ltext in sql_fstrings[:10]:
    print(f"Line {lno}: {ltext}")

# 4. SCAN FOR RATINGS / SCORES (0-5)
print("\n--- 4. Scanning for Rating / Review inputs bounds ---")
rating_matches = []
for idx, line in enumerate(lines):
    if any(k in line.lower() for k in ['rating', 'stars', 'score']) and any(c in line for c in ['data.get', 'request.json', 'request.form']):
        # check next 10 lines for 1-5 or 0-5 check
        snippet = "\n".join(lines[idx:min(len(lines), idx+10)])
        if not any(b in snippet for b in ['< 1', '< 0', '> 5', 'in [1, 2, 3, 4, 5]', 'in range']):
            rating_matches.append((idx+1, line.strip(), snippet))

print(f"Rating inputs without apparent 1-5 check: {len(rating_matches)}")
for lno, ltext, snip in rating_matches[:5]:
    print(f"Line {lno}: {ltext}")

# 5. SCAN FOR PHONE / CONTACT NUMBERS
print("\n--- 5. Scanning for Phone Number validation in backend ---")
phone_matches = []
for idx, line in enumerate(lines):
    if any(k in line.lower() for k in ['phone', 'contact_number', 'mobile']) and any(c in line for c in ['data.get', 'request.json', 'request.form']):
        snippet = "\n".join(lines[idx:min(len(lines), idx+8)])
        if "len(" not in snippet and "[:" not in snippet:
            phone_matches.append((idx+1, line.strip()))

print(f"Phone/contact assignments without length cap: {len(phone_matches)}")
for lno, ltext in phone_matches[:10]:
    print(f"Line {lno}: {ltext}")
