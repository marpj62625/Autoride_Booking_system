with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

pos_modal_line = 0
for i, l in enumerate(lines):
    if '#desktopCameraModal {' in l:
        pos_modal_line = i
        break

stack = []
for i in range(pos_modal_line):
    line = lines[i]
    for char in line:
        if char == '{':
            stack.append((i+1, line.strip()))
        elif char == '}':
            if stack:
                stack.pop()
            else:
                print(f"Extra close at line {i+1}")

print("Unclosed blocks before #desktopCameraModal:")
for s in stack:
    print(f"Line {s[0]}: {s[1]}")
