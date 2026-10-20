with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '@media (min-width: 768px)' in l:
        print(f"Line {i+1}: {l.strip()}")
        depth = 0
        for j in range(i, len(lines)):
            line = lines[j]
            for c in line:
                if c == '{': depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        print(f"Closes at line {j+1}: {line.strip()}")
                        break
            if depth == 0: break
        break
