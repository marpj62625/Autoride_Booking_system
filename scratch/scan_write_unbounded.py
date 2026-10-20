import re
import ast

with open("backend/app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Let's find all route handlers with POST/PUT/PATCH
route_pattern = re.compile(r"@app\.route\((['\"][^'\"]+['\"].*?)\)\s*\ndef\s+([a-zA-Z0-9_]+)\(([^)]*)\):([\s\S]*?)(?=(?:@app\.route|\Z))")
routes = route_pattern.findall(content)

print(f"Total routes matched: {len(routes)}")

findings = []

for r_dec, fn_name, args, fn_body in routes:
    if not any(m in r_dec for m in ['POST', 'PUT', 'PATCH', 'DELETE']):
        continue
    
    # 1. Check for request.json or request.form calls
    gets = re.findall(r"([a-zA-Z0-9_]+)\s*=\s*(?:data|request\.json|request\.form)\.get\(['\"]([a-zA-Z0-9_]+)['\"](?:,\s*([^)]+))?\)", fn_body)
    
    for var, key, default in gets:
        # Check if var is a text field that is directly passed to SQL or used without len() / [: / int / float / whitelist
        if any(term in key for term in ['reason', 'address', 'city', 'note', 'comment', 'description', 'title', 'subject', 'message', 'name', 'code', 'category', 'model', 'brand', 'fuel', 'transmission', 'type']):
            # check if bounded
            is_bounded = (f"len({var})" in fn_body or 
                          f"[:" in fn_body or 
                          f"int({var})" in fn_body or 
                          f"float({var})" in fn_body or
                          f"in [" in fn_body or
                          f"in (" in fn_body or
                          f"_validate" in fn_body)
            if not is_bounded:
                # check if this var is used in a cur.execute
                if f"%s" in fn_body and var in fn_body:
                    findings.append((fn_name, key, var))

print(f"Total potential unbounded text fields in write endpoints: {len(findings)}")
unique_findings = set(findings)
print(f"Unique endpoint/field combinations: {len(unique_findings)}")
for fn, k, v in sorted(list(unique_findings))[:25]:
    print(f"  {fn}(): field '{k}' (var '{v}')")
