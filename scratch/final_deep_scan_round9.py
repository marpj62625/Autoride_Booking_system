import re
import ast
import os
import sys

BACKEND_PATH = r"backend/app.py"
FRONTEND_HTML = r"frontend/index.html"
FRONTEND_JS = r"frontend/js/app.js"
ADMIN_HTML = r"admin_app/index.html"
ADMIN_JS = r"admin_app/js/app.js"

print("="*60)
print("ROUND 9: EXHAUSTIVE FINAL DATA VALIDATION AUDIT")
print("="*60)

with open(BACKEND_PATH, "r", encoding="utf-8") as f:
    backend_code = f.read()

# 1. Check for raw int() or float() calls on request parameters that could throw unhandled ValueError
# Find patterns like int(request.args.get(...)) or float(request.form.get(...))
raw_casts = []
pattern_casts = re.finditer(r'(int|float)\s*\(\s*(request\.(?:args|form|json|values)\.get\([^)]+\)|data\.get\([^)]+\))\s*\)', backend_code)
for m in pattern_casts:
    line_no = backend_code.count("\n", 0, m.start()) + 1
    raw_casts.append((line_no, m.group(0)))

print(f"\n[Backend Check 1] Unprotected int()/float() directly on request getters: {len(raw_casts)}")
for line, match in raw_casts:
    print(f"  Line {line}: {match}")

# 2. Check for strptime calls on request data without try-except or safe wrapper
raw_strptimes = []
pattern_strptime = re.finditer(r'datetime\.strptime\s*\([^,\n]+,\s*["\'][^"\']+["\']\)', backend_code)
for m in pattern_strptime:
    line_no = backend_code.count("\n", 0, m.start()) + 1
    # Check context around line_no for try/except
    lines = backend_code.split("\n")
    start_context = max(0, line_no - 15)
    end_context = min(len(lines), line_no + 15)
    context = "\n".join(lines[start_context:end_context])
    if "try:" not in context or "except" not in context:
        # Check if line itself has a safe fallback or default
        raw_strptimes.append((line_no, lines[line_no-1].strip()))

print(f"\n[Backend Check 2] strptime calls outside immediate try-except blocks: {len(raw_strptimes)}")
for line, match in raw_strptimes:
    print(f"  Line {line}: {match}")

# 3. Check for unbounded string insertions in new routes or user inputs
# Look for request.form.get or request.json.get assigned to variables without [:LIMIT] or strip()[:LIMIT]
# Let's inspect write endpoints (POST, PUT, PATCH, DELETE)
endpoints = re.findall(r'@app\.route\s*\(\s*["\']([^"\']+)["\'][^)]*methods\s*=\s*\[([^\]]+)\]', backend_code)
print(f"\n[Backend Check 3] Total routes registered: {len(endpoints)}")

# 4. Check all file upload endpoints in backend
file_endpoints = []
for m in re.finditer(r'request\.files\.get\s*\(\s*["\']([^"\']+)["\']\)|request\.files\[["\']([^"\']+)["\']\]', backend_code):
    line_no = backend_code.count("\n", 0, m.start()) + 1
    field_name = m.group(1) or m.group(2)
    # Check if allowed_file or reject_non_image or secure_filename or content_type is near
    lines = backend_code.split("\n")
    ctx = "\n".join(lines[max(0, line_no-10):min(len(lines), line_no+20)])
    has_check = any(w in ctx for w in ['allowed_file', 'reject_non_image', 'allowed_file_or_pdf', 'content_type', 'mimetype', '.filename.rsplit'])
    file_endpoints.append((line_no, field_name, has_check))

print(f"\n[Backend Check 4] File upload handlers total: {len(file_endpoints)}")
unprotected_files = [f for f in file_endpoints if not f[2]]
print(f"  Unprotected file upload handlers: {len(unprotected_files)}")
for line, field, _ in unprotected_files:
    print(f"  Line {line}: Field '{field}' has no visible extension/MIME check")

# 5. Check item #6 constraint: max_booking_duration_days
print("\n[Constraint Check] Item #6 (max_booking_duration_days):")
matches_item6 = re.findall(r'max_booking_duration_days', backend_code)
print(f"  Occurrences of 'max_booking_duration_days': {len(matches_item6)}")

# 6. Check frontend HTML inputs for missing maxlength or bounds
def check_html_inputs(filepath, name):
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
    inputs = re.findall(r'<input\s+[^>]*>', html, re.IGNORECASE)
    unbounded = []
    for inp in inputs:
        # Ignore hidden, submit, button, checkbox, radio, file (handled separately)
        if re.search(r'type=["\'](?:hidden|submit|button|checkbox|radio|file)["\']', inp, re.IGNORECASE):
            continue
        # If text/email/tel/password/search/number/date
        has_limit = (
            'maxlength=' in inp.lower() or 
            'max=' in inp.lower() or 
            'readonly' in inp.lower() or 
            'disabled' in inp.lower()
        )
        if not has_limit:
            unbounded.append(inp.strip())
    print(f"\n[{name}] Total evaluated inputs: {len(inputs)} | Unbounded: {len(unbounded)}")
    for u in unbounded[:10]:
        print(f"  Unbounded: {u}")
    return unbounded

check_html_inputs(FRONTEND_HTML, "Customer HTML")
check_html_inputs(ADMIN_HTML, "Admin HTML")

print("\n" + "="*60)
print("ROUND 9 AUDIT INITIAL RUN COMPLETE")
print("="*60)
