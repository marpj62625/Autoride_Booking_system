with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if 'pastBookingsSort' in line:
        print(f'pastBookingsSort: line {idx+1}: {line.strip()[:100]}')
    if 'id="tabNew"' in line:
        print(f'tabNew: line {idx+1}: {line.strip()[:100]}')
    if 'id="tabAll"' in line:
        print(f'tabAll: line {idx+1}: {line.strip()[:100]}')
    if 'id="verificationsList"' in line or 'id="verifications"' in line:
        print(f'verifications: line {idx+1}: {line.strip()[:100]}')
    if 'id="users"' in line and '<div' in line:
        print(f'users container: line {idx+1}: {line.strip()[:100]}')
    if 'const Bookings = {' in line:
        print(f'const Bookings: line {idx+1}')
    if 'const Verifications = {' in line:
        print(f'const Verifications: line {idx+1}')
    if 'const UserMgmt = {' in line:
        print(f'const UserMgmt: line {idx+1}')
