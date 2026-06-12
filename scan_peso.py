
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

SKIP_DIRS = {'node_modules', '.git', '__pycache__', '.gradle', 'build', '.idea', 'venv', 'scratch'}
EXTENSIONS = ('.js', '.html', '.css', '.py')

# Peso sign ₱ in UTF-8 is E2 82 B1
# If broken, it might be stored as:
# - 0xA7 (Windows-1252 § sign used instead)
# - 0x80 (Windows-1252 euro sign €)
# - Just '?' or showing as diamond-?
# - Or the raw bytes got corrupted

results = {}

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for fname in files:
        if not fname.endswith(EXTENSIONS):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, 'rb') as f:
                raw = f.read()
        except Exception:
            continue

        hits = []

        # Check 1: Look for '?' near currency context (Refund, Amount, Price, Payment, Total)
        text = raw.decode('utf-8', errors='replace')
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if '?' in line:
                lower = line.lower()
                if any(kw in lower for kw in ['amount', 'price', 'refund', 'total', 'payment', 'peso', 'php', 'fare', 'fee', 'cost', 'rate', 'earn']):
                    # Check if the ? is likely a broken peso sign
                    idx = line.find('?')
                    while idx != -1:
                        # Check context around ?
                        ctx = line[max(0,idx-10):idx+15]
                        # Skip if it's a legit ? (like conditional operators, ternary, regex)
                        surrounding = line[max(0,idx-2):idx+3]
                        if not any(op in surrounding for op in ['?.', '??', '?:', '/*', '*/', '//']):
                            hits.append(f'  line {i+1}: {line.strip()[:120]}')
                        idx = line.find('?', idx+1)

        if hits:
            results[fpath] = hits[:5]

print(f'Files with possible broken peso sign (?):\n')
for fpath, lines in sorted(results.items()):
    print(f'FILE: {fpath}')
    for l in lines:
        print(l)
    print()
