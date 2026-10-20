import re

with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    code = f.read()
    lines = code.splitlines()

def find_route_block(route_substr):
    results = []
    in_route = False
    start_idx = 0
    route_name = ""
    block_lines = []
    
    for idx, line in enumerate(lines):
        if ('@app.route' in line or '@admin_bp.route' in line) and route_substr in line:
            start_idx = idx
            in_route = True
            route_name = line.strip()
            block_lines = [line]
            continue
        if in_route:
            block_lines.append(line)
            # Route block usually ends at next unindented @ or def
            if idx > start_idx + 1 and (line.startswith('@app.route') or line.startswith('def ') and not line.startswith('    def ')):
                results.append((start_idx + 1, route_name, '\n'.join(block_lines[:-1])))
                in_route = False
                block_lines = []
    return results

critical_routes = [
    '/book',
    '/modify-booking',
    '/extend',
    '/cancel',
    '/verify-otp',
    '/reset-password',
    '/driver-license',
    '/payment'
]

print("=== SCANNING CRITICAL TRANSACTION ROUTES ===")
for r in critical_routes:
    found = find_route_block(r)
    print(f"\nTarget: {r} -> Found {len(found)} instances")
    for start_line, rname, block in found[:2]:
        print(f"  Line {start_line}: {rname}")
        # Check specific validation patterns in block
        has_try = 'try:' in block
        has_date_val = 'strptime' in block or 'validate_date' in block or 'start_date' in block
        has_price_val = 'price' in block
        print(f"    Block size: {len(block.splitlines())} lines | try-except: {has_try} | date_handling: {has_date_val} | price_handling: {has_price_val}")
