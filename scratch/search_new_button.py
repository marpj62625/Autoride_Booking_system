import os, re

for root, dirs, files in os.walk('.'):
    if '.git' in root or '.gradle' in root or 'node_modules' in root: continue
    for f in files:
        if f.endswith(('.html', '.js')):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
                for i, line in enumerate(c.splitlines()):
                    if '>New<' in line or '>New Bookings<' in line or 'data-filter="pending"' in line:
                        print(f"{p}:{i+1}: {line.strip()[:100]}")
