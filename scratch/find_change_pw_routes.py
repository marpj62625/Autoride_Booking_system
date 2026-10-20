with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f, 1):
        if ('change-password' in line.lower() or 'change_password' in line.lower() or 'update-password' in line.lower()) and '@app.route' in line:
            print(f"Line {idx}: {line.strip()[:100]}")
