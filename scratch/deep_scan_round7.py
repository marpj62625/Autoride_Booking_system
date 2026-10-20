import ast
import os
import re

print("=== DEEP SCAN ROUND 7 / EXHAUSTIVE SWEEP ===")

backend_path = "backend/app.py"
with open(backend_path, "r", encoding="utf-8") as f:
    backend_code = f.read()

lines = backend_code.split('\n')

# 1. SCAN ALL request.args.get across ALL endpoints
print("\n--- 1. Scanning ALL request.args.get() for ID and numeric params ---")
args_all = []
for idx, line in enumerate(lines):
    matches = re.finditer(r"([a-zA-Z0-9_]+)\s*=\s*request\.args\.get\(['\"]([a-zA-Z0-9_]+)['\"](?:,\s*([^)]+))?\)", line)
    for m in matches:
        var_name = m.group(1)
        param_name = m.group(2)
        default_val = m.group(3)
        # Check if parameter implies an ID or number
        if any(term in param_name.lower() for term in ['id', 'page', 'limit', 'count', 'offset', 'num', 'year', 'month', 'day']):
            snippet = "\n".join(lines[idx:min(len(lines), idx+12)])
            has_int = f"int({var_name})" in snippet or f"type=int" in line
            has_try = "try:" in snippet
            if not (has_int and has_try) and not ("type=int" in line):
                args_all.append((idx+1, param_name, var_name, line.strip()))

print(f"Unprotected numeric/ID request.args: {len(args_all)}")
for lno, pname, vname, ltext in args_all[:20]:
    print(f"  Line {lno}: param '{pname}' -> `{ltext}`")

# 2. SCAN ALL datetime.strptime calls in backend/app.py
print("\n--- 2. Scanning datetime.strptime() for unhandled ValueError ---")
strptime_calls = []
for idx, line in enumerate(lines):
    if "strptime(" in line:
        # Check preceding 15 lines for try block
        preceding = "\n".join(lines[max(0, idx-15):idx])
        if "try:" not in preceding:
            strptime_calls.append((idx+1, line.strip()))

print(f"Unprotected strptime calls: {len(strptime_calls)}")
for lno, ltext in strptime_calls:
    print(f"  Line {lno}: `{ltext}`")

# 3. SCAN ALL request.form.get and request.json.get for email fields
print("\n--- 3. Scanning Email fields across routes ---")
email_calls = []
for idx, line in enumerate(lines):
    if ("request.form.get('email'" in line or "data.get('email'" in line) and "def " not in line:
        snippet = "\n".join(lines[idx:min(len(lines), idx+10)])
        if "len(" not in snippet and "[:" not in snippet and "_validate" not in snippet:
            email_calls.append((idx+1, line.strip()))

print(f"Email fields without length check: {len(email_calls)}")
for lno, ltext in email_calls[:10]:
    print(f"  Line {lno}: `{ltext}`")

# 4. SCAN ALL request.form.get and request.json.get for password fields
print("\n--- 4. Scanning Password fields across routes ---")
pass_calls = []
for idx, line in enumerate(lines):
    if any(k in line for k in ["get('password'", "get('new_password'", "get('current_password'"]) and "def " not in line:
        snippet = "\n".join(lines[idx:min(len(lines), idx+10)])
        if "len(" not in snippet and "[:" not in snippet and "_validate" not in snippet:
            pass_calls.append((idx+1, line.strip()))

print(f"Password fields without length check: {len(pass_calls)}")
for lno, ltext in pass_calls[:10]:
    print(f"  Line {lno}: `{ltext}`")
