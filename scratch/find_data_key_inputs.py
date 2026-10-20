with open('AutorideSystem/admin_app/index.html', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        if 'data-key=' in line and '<input' in line:
            print(f"Line {idx+1}: {line.strip()[:120]}")
        elif 'data-key=' in line and '<textarea' in line:
            print(f"Line {idx+1}: {line.strip()[:120]}")
