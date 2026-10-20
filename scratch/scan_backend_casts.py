import re

with open('AutorideSystem/backend/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines in backend/app.py: {len(lines)}")

# Look for patterns like float(data.get(...) or float(request.form.get(...))
patterns = [
    r'(?<!try:)\s+([a-zA-Z_0-9]+)\s*=\s*float\((?:data|request\.form|request\.args|form)\.get\(',
    r'(?<!try:)\s+([a-zA-Z_0-9]+)\s*=\s*int\((?:data|request\.form|request\.args|form)\.get\(',
]

for idx, line in enumerate(lines):
    # Check if this line does a direct cast of untrusted input
    if ('float(data.get(' in line or 'float(request.form.get(' in line or 'float(request.args.get(' in line) and 'try' not in line:
        print(f"Line {idx+1}: {line.strip()}")
