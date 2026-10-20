with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'id="page-more"' in line:
        print(f"Line {i+1}: {line.strip()}")
        for j in range(i+1, min(i+40, len(lines))):
            print(f"Line {j+1}: {lines[j].strip()}")
        break
