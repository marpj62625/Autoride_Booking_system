with open('backend/app.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '@app.route' in l and ('users/search' in l or '/admin/users' in l):
        print(f"Line {i+1}: {l.strip()}")
        for j in range(i, min(i+25, len(lines))):
            print(f"  {lines[j].strip()}")
        print("="*40)
