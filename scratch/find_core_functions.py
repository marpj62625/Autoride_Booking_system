with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f, 1):
        if 'insert into bookings' in line.lower():
            print(f"Line {idx}: {line.strip()[:100]}")
        elif 'def ' in line and ('book' in line.lower() or 'otp' in line.lower() or 'license' in line.lower() or 'extend' in line.lower()):
            print(f"Def Line {idx}: {line.strip()[:100]}")
