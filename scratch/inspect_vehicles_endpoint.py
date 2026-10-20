with open('backend/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "'/vehicles'" in line and 'GET' in line:
        print(f"Line {i+1}: {line.strip()}")
        for j in range(i, min(len(lines), i+35)):
            print(f"{j+1}: {lines[j]}", end='')
        break
