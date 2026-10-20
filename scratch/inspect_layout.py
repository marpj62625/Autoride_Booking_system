with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'id="settings"' in l:
        print(f"id=settings at line {i+1}: {l.strip()[:100]}")
    if 'id="fleet-calendar"' in l:
        print(f"id=fleet-calendar at line {i+1}: {l.strip()[:100]}")
    if 'id="verifications"' in l:
        print(f"id=verifications at line {i+1}: {l.strip()[:100]}")
