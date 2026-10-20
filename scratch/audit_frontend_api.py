import re

with open("admin_app/index.html", "r", encoding="utf-8", errors="ignore") as f:
    html_content = f.read()

with open("backend/app.py", "r", encoding="utf-8", errors="ignore") as f:
    backend_content = f.read()

# 1. Extract all fetch endpoints in index.html
fetch_patterns = re.findall(r'fetch\([`"\']([^`"\']+)[\'"`]', html_content)
api_calls = re.findall(r'apiFetch\([`"\']([^`"\']+)[\'"`]', html_content)
all_calls = set(fetch_patterns + api_calls)

print(f"Total API/Fetch endpoints found in admin_app/index.html: {len(all_calls)}")

# Extract backend route strings from app.py
backend_routes = re.findall(r"@app\.route\([\'\"]([^\'\"]+)[\'\"]", backend_content)
print(f"Total backend @app.route definitions in app.py: {len(backend_routes)}")

# Helper to normalize route pattern (replace <int:...> etc. with placeholder)
def normalize_route(r):
    r = re.sub(r'<[^>]+>', '{param}', r)
    return r.strip('/')

normalized_backend = set(normalize_route(r) for r in backend_routes)

unmatched = []
for c in sorted(all_calls):
    # strip base URL templates like ${API_BASE}, ${API_URL}, http...
    cleaned = re.sub(r'https?://[^/]+', '', c)
    cleaned = re.sub(r'^\$\{[^}]+\}', '', cleaned)
    cleaned = cleaned.split('?')[0] # remove query params
    cleaned = re.sub(r'\$\{[^}]+\}', '{param}', cleaned)
    norm = cleaned.strip('/')
    
    if not norm:
        continue

    # Check if norm matches any backend route
    matched = False
    for b in normalized_backend:
        if norm == b:
            matched = True
            break
        # Also check without leading 'api/'
        if norm.startswith('api/') and norm[4:] == b:
            matched = True
            break
        if b.startswith('api/') and norm == b[4:]:
            matched = True
            break
            
    if not matched:
        unmatched.append((c, norm))

print(f"\n--- POTENTIALLY BROKEN/MISSING ENDPOINTS CALLED BY FRONTEND ({len(unmatched)}) ---")
for raw, norm in unmatched:
    print(f"Frontend calls: {raw}  --> Normalized: {norm}")
