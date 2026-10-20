with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def print_range(start, end, title):
    print(f'=== {title} (lines {start} to {end}) ===')
    for i in range(start-1, min(end, len(lines))):
        print(f'{i+1}: {lines[i]}', end='')
    print()

print_range(5875, 5925, 'tabActive HTML')
print_range(26810, 26900, 'tabActive JS')
