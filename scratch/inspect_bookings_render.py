with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def print_range(start, end, title):
    print(f'=== {title} (lines {start} to {end}) ===')
    for i in range(start-1, min(end, len(lines))):
        print(f'{i+1}: {lines[i]}', end='')
    print()

print_range(18640, 18730, 'Bookings renderNew')
print_range(18940, 19030, 'Bookings render')
