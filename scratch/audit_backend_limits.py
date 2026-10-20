import re

with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

routes = []
curr_route = None

for idx, line in enumerate(lines, 1):
    rm = re.search(r'@(?:app|api|bp)\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods=\[([^\]]+)\])?', line)
    if rm:
        endpoint = rm.group(1)
        methods = rm.group(2) if rm.group(2) else "'GET'"
        curr_route = {'line': idx, 'endpoint': endpoint, 'methods': methods.replace('"', '').replace("'", '').strip(), 'inputs': []}
        routes.append(curr_route)
    elif curr_route and ('data.get(' in line or 'request.json.get(' in line or 'request.form.get(' in line or 'request.args.get(' in line):
        m = re.search(r'(?:data|request\.json|request\.form|request\.args)\.get\([\'"]([^\'"]+)[\'"]', line)
        if m:
            field = m.group(1)
            if field not in curr_route['inputs']:
                curr_route['inputs'].append(field)

print(f"Total backend endpoints found: {len(routes)}")
with open('scratch/backend_routes_inputs.txt', 'w', encoding='utf-8') as out:
    for r in routes:
        if r['inputs']:
            out.write(f"Line {r['line']:<5} {r['methods']:<15} {r['endpoint']:<35} Inputs: {', '.join(r['inputs'])}\n")

print("Written to scratch/backend_routes_inputs.txt")
