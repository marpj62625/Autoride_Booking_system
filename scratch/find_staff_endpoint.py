with open('admin_app/index.html', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f, 1):
        if 'staffName' in line:
            print(f"Line {idx}: {line.strip()[:100]}")
