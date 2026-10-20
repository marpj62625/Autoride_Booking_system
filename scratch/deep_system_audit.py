import re
import os
import ast

BACKEND_FILE = 'backend/app.py'

def audit_backend():
    print("=" * 80)
    print("1. AUDITING BACKEND (backend/app.py)")
    print("=" * 80)
    
    with open(BACKEND_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    full_text = "".join(lines)
    
    # Check 1: Raw SQL formatting / injection risks
    print("\n--- Check 1.1: Direct SQL String Formatting (cur.execute with % or .format or f-strings) ---")
    sql_issues = []
    for idx, line in enumerate(lines):
        if re.search(r'cur\.execute\s*\(\s*f["\']', line) or re.search(r'cur\.execute\s*\([^,]+%\s*\(?', line):
            # Exclude lines that only format table names safely if parameterized
            sql_issues.append((idx + 1, line.strip()))
    print(f"Found {len(sql_issues)} potential SQL injection / string-formatting points:")
    for lnum, code in sql_issues[:15]:
        print(f"  Line {lnum}: {code[:100]}")
    if len(sql_issues) > 15:
        print(f"  ... and {len(sql_issues) - 15} more.")

    # Check 2: Auth bypasses in sensitive routes (POST, PUT, DELETE without token / admin check)
    print("\n--- Check 2: Sensitive Endpoints with Inadequate Auth / Fallbacks ---")
    route_pattern = re.compile(r'(@app\.route\([^)]+\)\s*)+def\s+([a-zA-Z0-9_]+)\s*\([^)]*\):')
    
    # We can inspect function blocks
    func_starts = []
    for idx, line in enumerate(lines):
        m = re.match(r'def\s+([a-zA-Z0-9_]+)\s*\(', line)
        if m:
            func_starts.append((idx, m.group(1)))
            
    sensitive_findings = []
    for i in range(len(func_starts)):
        start_idx, func_name = func_starts[i]
        end_idx = func_starts[i+1][0] if i+1 < len(func_starts) else len(lines)
        func_lines = lines[start_idx:end_idx]
        func_text = "".join(func_lines)
        
        # Check preceding decorators
        decs = []
        d_idx = start_idx - 1
        while d_idx >= 0 and (lines[d_idx].strip().startswith('@') or lines[d_idx].strip() == ''):
            if lines[d_idx].strip().startswith('@'):
                decs.insert(0, lines[d_idx].strip())
            d_idx -= 1
            
        is_route = any('@app.route' in d for d in decs)
        if not is_route:
            continue
            
        routes_str = " ".join(decs)
        is_admin_route = '/admin' in routes_str
        is_mutating = any(m in routes_str for m in ['POST', 'PUT', 'DELETE'])
        
        # Check fallback patterns like: admin_fallback or omitting admin check
        if 'admin_fallback' in func_text or 'SELECT * FROM users WHERE role' in func_text:
            sensitive_findings.append({
                'type': 'CRITICAL_AUTH_FALLBACK',
                'func': func_name,
                'line': start_idx + 1,
                'routes': routes_str,
                'desc': 'Endpoint falls back to querying first admin in DB if requester_id/token is missing!'
            })
            
        # Check DELETE routes without session / token / role verification
        if 'DELETE' in routes_str:
            has_auth = any(k in func_text for k in ['token_required', 'admin_required', 'get_jwt', 'session.get', 'verify_admin', 'role == \'admin\'', 'role == "admin"'])
            if not has_auth:
                sensitive_findings.append({
                    'type': 'UNPROTECTED_DELETE',
                    'func': func_name,
                    'line': start_idx + 1,
                    'routes': routes_str,
                    'desc': 'DELETE endpoint lacks admin/token validation check.'
                })
                
        # Check sensitive state mutations (approve booking, complete booking, reset password)
        for sensitive_word in ['reset-password', 'approve', 'complete', 'verify-action', 'process-refund']:
            if sensitive_word in routes_str:
                has_strict_auth = any(k in func_text for k in ['token_required', 'admin_required', 'verify_token', 'session.get', 'role in [', 'role == \'admin\'', 'role == "admin"'])
                # Also check if it trusts client passed admin_id without validating
                trusts_client_id = ('data.get(\'admin_id\')' in func_text or "data.get('requester_id')" in func_text or "request.args.get('admin_id')" in func_text) and not has_strict_auth
                if trusts_client_id or not has_strict_auth:
                    sensitive_findings.append({
                        'type': f'UNPROTECTED_{sensitive_word.upper().replace("-", "_")}',
                        'func': func_name,
                        'line': start_idx + 1,
                        'routes': routes_str,
                        'desc': f'Sensitive action "{sensitive_word}" can be executed without authenticated session/token or trusts client-supplied admin_id.'
                    })

    for f in sensitive_findings:
        print(f"[{f['type']}] Line {f['line']} ({f['func']}): {f['desc']}\n  Routes: {f['routes'][:110]}\n")

    # Check 3: Business Logic & Price Tampering in Booking Creation
    print("\n--- Check 3: Business Logic / Price Tampering in /api/book ---")
    book_func = [f for f in func_starts if f[1] == 'create_booking' or f[1] == 'book_vehicle' or f[1] == 'book']
    for idx, fname in func_starts:
        if fname in ['create_booking', 'book_car', 'book']:
            print(f"Examining {fname} at line {idx+1}")
            sub_lines = lines[idx:idx+150]
            for s_idx, l in enumerate(sub_lines):
                if any(p in l for p in ['total_price =', 'base_price =', 'points_earned =', 'amount_paid =', 'balance_amount =']):
                    print(f"  Line {idx + 1 + s_idx}: {l.strip()}")

if __name__ == '__main__':
    audit_backend()
