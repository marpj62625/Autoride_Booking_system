with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f, 1):
        if 'booking_extensions' in line or 'extension' in line:
            if '@app.route' in line or 'INSERT INTO' in line or 'SELECT' in line:
                print(f"Line {idx}: {line.strip()[:100]}")
