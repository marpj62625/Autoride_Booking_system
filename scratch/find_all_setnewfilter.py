with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'Bookings.setNewFilter' in line:
        print(f"Line {i+1}: {line.strip()}")
