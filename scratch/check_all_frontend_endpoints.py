import os
import re
import sys

# Extract all routes from the app
sys.path.insert(0, 'backend')
from app import app

registered_routes = set()
for rule in app.url_map.iter_rules():
    # normalize rule: remove parameter placeholders like <int:id> -> {param}
    r = re.sub(r'<[^>]+>', '{param}', rule.rule)
    registered_routes.add(r)
    # also add with and without trailing slash
    registered_routes.add(r.rstrip('/'))
    # also add without leading /api if present, and with leading /api if not present
    if r.startswith('/api/'):
        registered_routes.add(r[4:])
    else:
        registered_routes.add('/api' + r)

print(f"Loaded {len(registered_routes)} normalized route patterns.")

# Scan mobile and web frontends
frontends = ['customer_mobile', 'admin_mobile', 'admin_app', 'frontend', 'car-rental']
api_call_regex = re.compile(r'[\'"`]((?:/api/|/admin/|/bookings/|/vehicles/|/users/|/auth/|/drivers/)[a-zA-Z0-9_\-/\${}]+)[\'"`]')

all_missing = []

for fe in frontends:
    if not os.path.exists(fe):
        continue
    for root, _, files in os.walk(fe):
        if any(skip in root for skip in ['node_modules', '.git', 'build', '.gradle', 'dist']):
            continue
        for file in files:
            if not file.endswith(('.js', '.ts', '.jsx', '.tsx', '.dart', '.html', '.vue')):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Search for endpoint patterns
                for match in api_call_regex.finditer(content):
                    endpoint = match.group(1)
                    # normalize
                    clean_ep = re.sub(r'\$\{[^}]+\}', '{param}', endpoint)
                    clean_ep = re.sub(r'\?.*$', '', clean_ep) # strip query string
                    clean_ep = clean_ep.rstrip('/')
                    
                    # check match
                    # check if clean_ep or clean_ep with / matches any registered route
                    matched = False
                    for r in registered_routes:
                        # simple pattern match
                        r_clean = r.rstrip('/')
                        if clean_ep == r_clean:
                            matched = True
                            break
                        # regex check if {param}
                        r_regex = '^' + re.sub(r'\\\{param\\\}', r'[^/]+', re.escape(r_clean)) + '$'
                        if re.match(r_regex, clean_ep):
                            matched = True
                            break
                            
                    if not matched:
                        # Exclude asset paths like /admin/img, /admin/css, /vehicles/images static files
                        if any(asset in clean_ep for asset in ['.png', '.jpg', '.jpeg', '.svg', '.css', '.js', '/css/', '/js/', '/images/']):
                            continue
                        all_missing.append((fe, file, endpoint, clean_ep))
            except Exception as e:
                pass

print(f"\n--- POTENTIALLY UNMATCHED/BROKEN ENDPOINTS IN FRONTENDS ({len(all_missing)}) ---")
seen = set()
for fe, file, raw, clean in all_missing:
    if clean not in seen:
        seen.add(clean)
        print(f"[{fe}] {file} calls '{raw}' (normalized: '{clean}')")
