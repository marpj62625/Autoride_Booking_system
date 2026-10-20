with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def print_range(start, end, title):
    print(f'=== {title} (lines {start} to {end}) ===')
    for i in range(start-1, min(end, len(lines))):
        print(f'{i+1}: {lines[i]}', end='')
    print()

print_range(5985, 6010, 'Past Bookings Sort')
print_range(6325, 6355, 'tabNew Header')
print_range(6485, 6515, 'tabAll Header')
print_range(6590, 6670, 'Verifications Header & Container')
print_range(10035, 10085, 'UserMgmt Search & Filter HTML')
