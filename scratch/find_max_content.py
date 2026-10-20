with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f, 1):
        if 'MAX_CONTENT_LENGTH' in line:
            print(f"Line {idx}: {line.strip()}")
