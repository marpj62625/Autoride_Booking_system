with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def print_range(start, end, title):
    print(f'=== {title} (lines {start} to {end}) ===')
    for i in range(start-1, min(end, len(lines))):
        if lines[i].strip():
            print(f'{i+1}: {lines[i]}', end='')
    print()

print_range(6330, 6375, 'New Bookings Header & Chips')
print_range(6490, 6555, 'All Bookings Header & Chips')
