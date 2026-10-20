import os, re

for root, dirs, files in os.walk('.'):
    if '.git' in root or '.gradle' in root or 'node_modules' in root:
        continue
    for f in files:
        if f.endswith('.html'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
                for line in c.splitlines():
                    if '.apk' in line.lower():
                        print(f"{p}: {line.strip()[:100]}")
