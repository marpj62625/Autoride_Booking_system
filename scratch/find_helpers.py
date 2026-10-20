with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f, 1):
        if 'def reject_non_image' in line or 'def _validate_person_name_py' in line:
            print(f"Line {idx}: {line.strip()}")
