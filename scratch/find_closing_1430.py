with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

depth = 0
for i in range(1429, len(lines)):
    line = lines[i]
    for char in line:
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                print(f"Line 1430 closed at line {i+1}: {line.strip()}")
                break
    if depth == 0:
        break
if depth != 0:
    print(f"Never closed! Final depth={depth}")
