with open('backend/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

auth_checks = []
for idx, l in enumerate(lines, 1):
    low = l.lower()
    if 'headers.get' in low and 'auth' in low:
        auth_checks.append((idx, l.strip()))

print('Authorization header checks in backend/app.py:', len(auth_checks))
for idx, l in auth_checks:
    print(f'Line {idx}: {l}')
