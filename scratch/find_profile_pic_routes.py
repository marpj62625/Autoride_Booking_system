with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f, 1):
        if 'profile_picture' in line or 'profile-picture' in line or 'profile-photo' in line:
            print(f"Line {idx}: {line.strip()[:100]}")
