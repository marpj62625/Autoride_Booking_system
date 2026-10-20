with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print('Total lines in backend/app.py:', len(lines))

endpoints = [
    '/api/auth/register',
    '/api/auth/login',
    '/api/user/profile',
    '/api/user/driver-license',
    '/api/admin/walkin',
    '/api/vehicles',
    '/api/admin/newsletter',
    '/api/reviews',
    '/api/chat/send',
    '/api/bookings/refund-request',
    '/api/bookings/book'
]

for idx, line in enumerate(lines, 1):
    for ep in endpoints:
        if f"'{ep}'" in line or f'"{ep}"' in line:
            print(f"Line {idx}: {line.strip()[:100]}")
