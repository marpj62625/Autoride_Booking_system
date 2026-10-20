import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'id="tabAll"' in line:
        print(f"tabAll found at line {i+1}:")
        for j in range(i, min(len(lines), i+40)):
            print(f"{j+1}: {lines[j]}", end='')
            if 'bookingsList' in lines[j]:
                break
        break
