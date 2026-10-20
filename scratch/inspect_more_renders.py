with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def print_range(start, end, title):
    print(f'=== {title} (lines {start} to {end}) ===')
    for i in range(start-1, min(end, len(lines))):
        print(f'{i+1}: {lines[i]}', end='')
    print()

print_range(22020, 22090, 'Verifications render')
print_range(32660, 32720, 'UserMgmt _render')
