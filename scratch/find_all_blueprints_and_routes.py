import os, re

with open('backend/app.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print("Searching for routes or blueprint registrations in backend/app.py...")
for idx, line in enumerate(lines, 1):
    if '@' in line and 'route(' in line:
        # print if it looks like register, login, profile, license, walkin, newsletter, review, refund
        for k in ['register', 'login', 'profile', 'driver-license', 'walkin', 'newsletter', 'review', 'refund', 'booking']:
            if k in line.lower():
                print(f"Line {idx}: {line.strip()}")
                break
    elif 'register_blueprint' in line:
        print(f"Blueprint at Line {idx}: {line.strip()}")
