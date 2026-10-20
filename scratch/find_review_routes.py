with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f, 1):
        if 'review' in line.lower() and '@app.route' in line:
            print(f"Line {idx}: {line.strip()}")
