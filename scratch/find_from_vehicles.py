with open('backend/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'from vehicles' in line.lower():
        print(f"{i+1}: {line.strip()[:100]}")
