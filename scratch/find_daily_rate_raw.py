with open('backend/app.py', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'daily_rate_raw = data.get' in line:
            print(f"Line {idx}: {line.strip()}")
