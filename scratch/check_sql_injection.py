import re

with open('backend/app.py', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

unparam = []
for idx, line in enumerate(lines):
    stripped = line.strip()
    if 'cur.execute(' in stripped:
        if stripped.startswith('cur.execute(f"') or stripped.startswith("cur.execute(f'"):
            unparam.append((idx + 1, stripped))
        elif 'cur.execute("' in stripped or "cur.execute('" in stripped:
            if '%s' in stripped and not (', (' in stripped or ', [' in stripped or ', {' in stripped or ', tuple(' in stripped):
                # could be multi-line execute, check if tuple is on next line
                next_few = "".join([lines[j].strip() for j in range(idx, min(idx + 5, len(lines)))])
                if not any(sep in next_few for sep in [', (', ', [', ', {', ', tuple(']):
                    unparam.append((idx + 1, stripped))

print(f"Total potentially unparameterized queries: {len(unparam)}")
for lnum, text in unparam[:30]:
    print(f"Line {lnum}: {text[:100]}")
