import re

with open('AutorideSystem/backend/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines in backend/app.py: {len(lines)}")

# Find all routes with methods POST, PUT, DELETE, PATCH
routes = []
current_route_lines = []
current_routes = []
in_function = False
func_name = ""

for idx, line in enumerate(lines):
    if line.strip().startswith('@app.route('):
        m = re.search(r"@app\.route\(['\"]([^'\"]+)['\"].*methods=\[([^\]]+)\]", line)
        if m:
            r_path = m.group(1)
            r_methods = m.group(2)
            if any(method in r_methods for method in ['POST', 'PUT', 'DELETE', 'PATCH']):
                current_routes.append((idx+1, r_path, r_methods))
    elif line.strip().startswith('def ') and current_routes:
        func_name = line.strip().split('(')[0].replace('def ', '')
        routes.append((current_routes, func_name, idx+1))
        current_routes = []

print(f"Total write route functions found: {len(routes)}")

# Check each route for potential unvalidated inputs
unvalidated_findings = []

for r_info, fname, f_line in routes:
    # inspect the function body (next ~60 lines or until next @app.route / def at col 0)
    body_lines = []
    for i in range(f_line, min(len(lines), f_line + 80)):
        if lines[i].startswith('@app.route') or (lines[i].startswith('def ') and not lines[i].startswith('    ')):
            break
        body_lines.append(lines[i])
    body_text = "".join(body_lines)
    
    # Check 1: status assignment without whitelist
    status_assign = re.findall(r"(status|payment_status|booking_status)\s*=\s*data\.get\(['\"](status|payment_status)['\"]", body_text)
    if status_assign:
        if 'in [' not in body_text and 'not in' not in body_text:
            unvalidated_findings.append((fname, f_line, "STATUS_NOT_WHITELISTED", status_assign))

    # Check 2: direct sql execution of user input without length check
    direct_params = re.findall(r"([a-zA-Z_0-9]+)\s*=\s*(?:data|request\.form)\.get\(['\"]([a-zA-Z_0-9]+)['\"]\)", body_text)
    for var, key in direct_params:
        if any(term in key for term in ['reason', 'notes', 'comment', 'message', 'title', 'description', 'name', 'code']):
            # check if bounded with [:X] or len(var)
            if f"len({var})" not in body_text and f"[:" not in body_text:
                unvalidated_findings.append((fname, f_line, f"UNBOUNDED_TEXT_{key}", var))

print(f"\nPotential findings count: {len(unvalidated_findings)}")
for fname, f_line, kind, details in unvalidated_findings:
    print(f"Line {f_line} in {fname}(): [{kind}] -> {details}")
