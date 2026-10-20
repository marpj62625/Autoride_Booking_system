import re

def audit_file(filepath):
    print(f"=== AUDITING {filepath} ===")
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # 1. SQL Injections: cur.execute with f-string or % or .format
    sql_issues = []
    for idx, line in enumerate(lines, 1):
        if 'cur.execute(' in line:
            # check if f-string or string concat
            if re.search(r'cur\.execute\(\s*f["\']', line) or re.search(r'cur\.execute\(.*?\+.*?\)', line) or ('%' in line and 'execute(%s' not in line and 'execute("""' not in line and 'execute(\'\'\'' not in line and not line.strip().endswith('%s",') and not line.strip().endswith('%s\',')):
                sql_issues.append((idx, line.strip()[:100]))
    
    print(f"Potential SQL injection lines ({len(sql_issues)}):")
    for lno, text in sql_issues[:10]:
        print(f"  Line {lno}: {text}")
        
    # 2. Bare except / pass
    bare_excepts = []
    for idx, line in enumerate(lines, 1):
        if re.search(r'except(\s+Exception)?\s*:', line):
            # check next line
            if idx < len(lines) and 'pass' in lines[idx]:
                bare_excepts.append(idx)
    print(f"Silent error swallowing (except: pass): {len(bare_excepts)} instances")
    
    # 3. Connection leaks (connect without close)
    connects = [idx for idx, line in enumerate(lines, 1) if 'psycopg.connect' in line or 'psycopg2.connect' in line]
    print(f"Direct psycopg.connect calls outside database.py: {len(connects)} at lines: {connects[:10]}")

audit_file('backend/app.py')
audit_file('backend/fleet_import.py')
