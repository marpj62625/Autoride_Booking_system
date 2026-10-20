with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f, 1):
        if 'def register' in line.lower() or 'def auth' in line.lower() or 'def login' in line.lower():
            print(f"Line {idx}: {line.strip()}")
