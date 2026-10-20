with open('admin_app/index.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

searches = ['activitySearch', 'pastBookingsSearch', 'archivedBookingsSearch', 'verificationsSearch']

for idx, line in enumerate(lines, 1):
    for s in searches:
        if s in line:
            print(f"Line {idx}: {line.strip()[:120]}")
