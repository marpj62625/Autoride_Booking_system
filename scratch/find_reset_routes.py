with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f, 1):
        if ('forgot' in line.lower() or 'reset-password' in line.lower() or 'reset_password' in line.lower()) and '@app.route' in line:
            print(f"Line {idx}: {line.strip()[:100]}")
