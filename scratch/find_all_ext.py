with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f, 1):
        if 'booking_extensions' in line.lower():
            print(f"Line {idx}: {line.strip()[:100]}")
