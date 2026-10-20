import os
import re
import ast

print("=== STARTING DEEP DATA VALIDATION SCAN ===")

# 1. SCAN BACKEND FOR UNPROTECTED CASTS: int() or float() on request inputs without try-except
with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    backend_code = f.read()
    backend_lines = backend_code.splitlines()

print(f"Loaded backend/app.py ({len(backend_lines)} lines).")

# Regex to find direct int(request...) or float(request...) or int(data.get(...))
unprotected_casts = []
for idx, line in enumerate(backend_lines, 1):
    stripped = line.strip()
    # Skip comments
    if stripped.startswith('#'):
        continue
    # Check for direct cast on request or data without apparent try block
    if re.search(r'\b(int|float)\s*\(\s*(request\.(args|form|json|values)|data\.get)\b', stripped):
        unprotected_casts.append((idx, stripped))

print(f"\n[SCAN 1] Found {len(unprotected_casts)} direct int()/float() casts on request/data:")
for line_no, text in unprotected_casts[:20]:
    print(f"  Line {line_no}: {text}")

# 2. SCAN FOR SQL INJECTION PATTERNS (f-strings or % with SQL keywords in execute)
sql_vulns = []
for idx, line in enumerate(backend_lines, 1):
    stripped = line.strip()
    if 'cur.execute(' in stripped or 'cursor.execute(' in stripped:
        if ('f"""' in stripped or 'f\'\'\'' in stripped or 'f"' in stripped or 'f\'' in stripped) and not stripped.startswith('#'):
            sql_vulns.append((idx, stripped))
        elif ('%' in stripped and '%%' not in stripped and not stripped.startswith('#') and ('% (' in stripped or '% (' not in stripped)) and re.search(r'execute\s*\(\s*["\'].*%\s*\(', stripped):
            sql_vulns.append((idx, stripped))

print(f"\n[SCAN 2] SQL queries with f-string or string formatting in execute: {len(sql_vulns)}")
for line_no, text in sql_vulns:
    print(f"  Line {line_no}: {text}")

# 3. SCAN FOR ALL POST/PUT ROUTES IN BACKEND TO CHECK INPUT HANDLING
route_pattern = re.compile(r"@app\.route\(\s*['\"]([^'\"]+)['\"]\s*,\s*methods=\[([^\]]+)\]\)")
routes = []
for idx, line in enumerate(backend_lines, 1):
    m = route_pattern.search(line)
    if m:
        path, methods = m.group(1), m.group(2)
        if 'POST' in methods or 'PUT' in methods:
            routes.append((idx, path, methods))

print(f"\n[SCAN 3] Found {len(routes)} write routes (POST/PUT).")
