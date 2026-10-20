import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'renderNew(' in line or 'renderNew()' in line:
        print(f"renderNew definition around line {i+1}:")
        for j in range(i, min(len(lines), i+60)):
            print(f"{j+1}: {lines[j]}", end='')
            if lines[j].strip() == '},' or lines[j].strip() == '}':
                break
        print("\n")

for i, line in enumerate(lines):
    if 'sortBookings(' in line:
        print(f"sortBookings definition around line {i+1}:")
        for j in range(i, min(len(lines), i+50)):
            print(f"{j+1}: {lines[j]}", end='')
            if lines[j].strip() == '},' or (lines[j].strip() == '}' and 'return' in lines[j-1]):
                break
        print("\n")

for i, line in enumerate(lines):
    if 'setNewFilter(' in line and 'function' in line or 'setNewFilter(filter' in line or 'setNewFilter(filter,' in line or 'setNewFilter(f' in line:
        print(f"setNewFilter definition around line {i+1}:")
        for j in range(i, min(len(lines), i+25)):
            print(f"{j+1}: {lines[j]}", end='')
            if lines[j].strip() == '},' or lines[j].strip() == '}':
                break
        print("\n")
