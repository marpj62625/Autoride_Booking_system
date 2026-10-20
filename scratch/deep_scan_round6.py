import ast
import os
import re

print("=== ROUND 6 DEEP SCAN ===")

backend_path = "backend/app.py"
with open(backend_path, "r", encoding="utf-8") as f:
    backend_code = f.read()

lines = backend_code.split('\n')

# 1. SCAN FOR URL PATH TRAVERSAL OR UNCONSTRAINED STRING/PATH PARAMS
print("\n--- 1. Scanning Route Path Parameter Definitions ---")
path_params = re.findall(r"@app\.route\(['\"]([^'\"]*<[^>]+>[^'\"]*)['\"]", backend_code)
risky_params = []
for p in path_params:
    matches = re.findall(r"<([^>]+)>", p)
    for m in matches:
        if not m.startswith("int:"):
            risky_params.append((p, m))

print(f"Non-integer route parameters: {len(risky_params)}")
for p, m in risky_params:
    print(f"  Route `{p}` -> Param `{m}`")

# 2. SCAN FOR QUERY PARAMETERS (request.args) USED IN SQL OR PARSERS
print("\n--- 2. Scanning Query Parameters (request.args) ---")
arg_matches = []
for idx, line in enumerate(lines):
    m = re.search(r"([a-zA-Z0-9_]+)\s*=\s*request\.args\.get\(['\"]([a-zA-Z0-9_]+)['\"](?:,\s*([^)]+))?\)", line)
    if m:
        var_name = m.group(1)
        param_name = m.group(2)
        default_val = m.group(3)
        # Check context around this line (next 15 lines)
        snippet = "\n".join(lines[idx:min(len(lines), idx+15)])
        # Check if used in cur.execute or date parsing or int parsing
        has_int_guard = f"int({var_name})" in snippet and "try:" in snippet
        has_len_guard = f"[:" in snippet or f"len({var_name})" in snippet
        has_whitelist = "in [" in snippet or "in (" in snippet or "==" in snippet
        is_safe = has_int_guard or has_len_guard or has_whitelist
        if not is_safe and ("cur.execute" in snippet or "strptime" in snippet or "datetime" in snippet):
            arg_matches.append((idx+1, param_name, var_name, line.strip()))

print(f"Query parameters with potential missing guards: {len(arg_matches)}")
for lno, pname, vname, ltext in arg_matches[:15]:
    print(f"Line {lno}: param '{pname}' (var '{vname}') -> `{ltext}`")

# 3. SCAN FOR LIST / ARRAY INPUTS (e.g. data.get('addons'), etc.)
print("\n--- 3. Scanning for JSON List / Array Handling ---")
list_matches = []
for idx, line in enumerate(lines):
    if any(k in line.lower() for k in ['items', 'addons', 'ids', 'vehicles', 'dates', 'records', 'photos', 'files']) and "data.get" in line:
        snippet = "\n".join(lines[idx:min(len(lines), idx+12)])
        if "isinstance" not in snippet:
            list_matches.append((idx+1, line.strip()))

print(f"List/Array inputs without isinstance check: {len(list_matches)}")
for lno, ltext in list_matches[:10]:
    print(f"Line {lno}: `{ltext}`")

# 4. SCAN OTHER BACKEND PYTHON FILES
print("\n--- 4. Scanning Other Backend Files ---")
other_files = ["backend/fleet_import.py", "backend/notification_service.py"]
for of in other_files:
    if os.path.exists(of):
        with open(of, "r", encoding="utf-8") as f:
            code = f.read()
        print(f"File {of}: {len(code.splitlines())} lines")
        # Check for direct SQL string interpolation
        f_execs = re.findall(r"execute\(f['\"][^'\"]*\{[^}]+\}[^'\"]*['\"]\)", code)
        print(f"  Direct f-string SQL executions in {of}: {len(f_execs)}")
