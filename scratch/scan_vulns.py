import re

with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print(f"Auditing backend/app.py ({len(lines)} lines)...")

findings = []

for idx, line in enumerate(lines):
    line_num = idx + 1
    s = line.strip()

    # 1. Check for raw SQL interpolation
    if 'cur.execute(' in s:
        # Check if f-string or string formatting
        if s.startswith('cur.execute(f"') or s.startswith("cur.execute(f'") or 'cur.execute(f"""' in s:
            findings.append({
                "type": "SQL_INJECTION_RISK",
                "severity": "HIGH",
                "line": line_num,
                "detail": s[:140]
            })
        elif re.search(r'cur\.execute\([^,]+%\s*\(', s):
            findings.append({
                "type": "SQL_INJECTION_RISK",
                "severity": "HIGH",
                "line": line_num,
                "detail": s[:140]
            })

    # 2. Check for unsafe file uploads / open without safe path
    if 'save(' in s and 'request.files' in ''.join(lines[max(0, idx-5):idx+5]):
        findings.append({
            "type": "FILE_UPLOAD_PATH",
            "severity": "MEDIUM",
            "line": line_num,
            "detail": s[:140]
        })

    # 3. Check for hardcoded secrets or keys
    if re.search(r'(secret_key|jwt_secret|api_key|password)\s*=\s*["\'][a-zA-Z0-9_-]{8,}["\']', s, re.IGNORECASE):
        if not s.startswith('#') and 'os.getenv' not in s and 'environ' not in s:
            findings.append({
                "type": "HARDCODED_SECRET",
                "severity": "CRITICAL",
                "line": line_num,
                "detail": s[:140]
            })

    # 4. Check for eval, exec, pickle, os.system, subprocess with shell=True
    if 'eval(' in s or 'exec(' in s or 'os.system(' in s or 'shell=True' in s:
        if not s.startswith('#'):
            findings.append({
                "type": "COMMAND_EXECUTION",
                "severity": "CRITICAL",
                "line": line_num,
                "detail": s[:140]
            })

print(f"Total findings from pattern scan: {len(findings)}")
for f_item in findings[:30]:
    print(f"[{f_item['severity']}] {f_item['type']} at line {f_item['line']}: {f_item['detail']}")
