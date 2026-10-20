with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def print_range(start, end, title):
    print(f'=== {title} (lines {start} to {end}) ===')
    for i in range(start-1, min(end, len(lines))):
        print(f'{i+1}: {lines[i]}', end='')
    print()

# Bookings object structure
print_range(18458, 18510, 'Bookings Object Start')
print_range(18655, 18710, 'Bookings renderNew')
print_range(18950, 19005, 'Bookings render')

# Verifications object structure
print_range(21908, 22060, 'Verifications Object')

# UserMgmt object structure
print_range(32470, 32660, 'UserMgmt Object')
