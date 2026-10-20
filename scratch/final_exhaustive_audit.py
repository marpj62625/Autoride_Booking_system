import re
import os

print("=== FINAL DEFINITIVE DATA VALIDATION AUDIT ===")

# 1. FRONTEND AUDIT
frontend_files = [
    ("customer_mobile/www/index.html", "Customer HTML"),
    ("customer_mobile/www/js/app.js", "Customer JS"),
    ("admin_app/index.html", "Admin HTML")
]

fe_unbounded = []
for fpath, label in frontend_files:
    if not os.path.exists(fpath): continue
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    matches = re.finditer(r'<input\s+([^>]+)>', content)
    for m in matches:
        tag = m.group(0)
        if any(f'type="{t}"' in tag for t in ['submit', 'button', 'checkbox', 'radio', 'hidden', 'file', 'color']):
            continue
        if 'maxlength' not in tag and 'max=' not in tag:
            lno = content[:m.start()].count('\n') + 1
            fe_unbounded.append((label, lno, tag[:80]))

print(f"\n1. Frontend Unbounded Inputs: {len(fe_unbounded)}")
for lbl, lno, snip in fe_unbounded:
    print(f"  [{lbl}] Line {lno}: `{snip}`")

# 2. BACKEND AUDIT
backend_path = "backend/app.py"
with open(backend_path, "r", encoding="utf-8") as f:
    backend_code = f.read()

lines = backend_code.split('\n')

# Check unsafe int/float casts
unsafe_casts = []
for idx, line in enumerate(lines):
    # Match int(...) or float(...) on request/data
    m = re.search(r"(int|float)\(((?:request\.(?:args|form|json|values)|data)\.get\(['\"][a-zA-Z0-9_]+['\"][^)]*\))", line)
    if not m:
        m = re.search(r"(int|float)\(((?:request\.(?:args|form|json|values)|data)\[['\"][a-zA-Z0-9_]+['\"]\])", line)
    if m:
        # Check if wrapped in try within 15 lines before
        preceding = "\n".join(lines[max(0, idx-15):idx])
        if "try:" not in preceding:
            unsafe_casts.append((idx+1, line.strip(), m.group(0)))

print(f"\n2. Backend Unprotected int/float Casts: {len(unsafe_casts)}")
for lno, ltext, ctext in unsafe_casts:
    print(f"  Line {lno}: {ctext} -> `{ltext}`")

# Check File Uploads without image/extension check
file_upload_issues = []
for idx, line in enumerate(lines):
    if "request.files[" in line or "request.files.get(" in line:
        snippet = "\n".join(lines[idx:min(len(lines), idx+15)])
        has_ext = any(k in snippet for k in ['ALLOWED_EXTENSIONS', 'allowed_file', 'endswith', 'splitext', 'reject_non_image', 'is_allowed_image'])
        if not has_ext:
            file_upload_issues.append((idx+1, line.strip()))

print(f"\n3. File Uploads Missing Extension/MIME Checks: {len(file_upload_issues)}")
for lno, ltext in file_upload_issues:
    print(f"  Line {lno}: `{ltext}`")

# Check Status updates without whitelist
status_issues = []
for idx, line in enumerate(lines):
    if ("status = data.get('status')" in line or "status = request.json.get('status')" in line) and "def " not in line:
        snippet = "\n".join(lines[idx:min(len(lines), idx+15)])
        if "in [" not in snippet and "in (" not in snippet and "== " not in snippet:
            status_issues.append((idx+1, line.strip()))

print(f"\n4. Status Assignments Missing Whitelist: {len(status_issues)}")
for lno, ltext in status_issues:
    print(f"  Line {lno}: `{ltext}`")

# Check SQL query formatting without parameters (%s)
sql_injections = []
for idx, line in enumerate(lines):
    if ("cur.execute(f\"" in line or "cur.execute(f'" in line) and "%s" not in line:
        sql_injections.append((idx+1, line.strip()))

print(f"\n5. Potential SQL Format Injections: {len(sql_injections)}")
for lno, ltext in sql_injections:
    print(f"  Line {lno}: `{ltext}`")
