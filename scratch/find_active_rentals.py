with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if 'Active Rentals' in line or 'tabActive' in line or 'ActiveBookings' in line or 'activeRentals' in line:
        print(f'line {idx+1}: {line.strip()[:120]}')
