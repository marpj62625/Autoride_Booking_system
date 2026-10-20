import re

with open('AutorideSystem/backend/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines in backend/app.py: {len(lines)}")

print("\n--- [1] datetime.strptime calls in backend/app.py ---")
for idx, l in enumerate(lines):
    if 'strptime(' in l:
        print(f"Line {idx+1}: {l.strip()[:100]}")

print("\n--- [2] Direct int/float on request.args in backend/app.py ---")
for idx, l in enumerate(lines):
    if ('int(request.args' in l or 'float(request.args' in l) and 'try' not in l:
        print(f"Line {idx+1}: {l.strip()[:100]}")

print("\n--- [3] Direct int on request.form or request.json in backend/app.py without try ---")
for idx, l in enumerate(lines):
    if ('int(data.get(' in l or 'int(request.form.get(' in l) and 'try' not in l:
        print(f"Line {idx+1}: {l.strip()[:100]}")

print("\n--- [4] SQL string interpolation (f-strings with SELECT/UPDATE/DELETE/INSERT) ---")
for idx, l in enumerate(lines):
    if re.search(r'cur\.execute\(\s*f["\']', l):
        print(f"Line {idx+1}: {l.strip()[:100]}")
