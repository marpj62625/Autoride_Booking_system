import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# 1. Find tabNew chips
for i, line in enumerate(lines):
    if 'id="tabNew"' in line:
        print(f"\n--- Found id=\"tabNew\" at line {i+1} ---")
        for j in range(i, min(len(lines), i+65)):
            print(f"{j+1}: {lines[j]}", end='')
            if 'id="newBookingsList"' in lines[j]:
                break
        break

# 2. Find sortBookings
for i, line in enumerate(lines):
    if 'sortBookings(' in line:
        print(f"\n--- Found sortBookings at line {i+1} ---")
        for j in range(max(0, i-2), min(len(lines), i+65)):
            print(f"{j+1}: {lines[j]}", end='')
            if 'return sorted;' in lines[j] or 'return list;' in lines[j]:
                print(f"{j+2}: {lines[j+1]}", end='')
                break
        break

# 3. Find renderNew
for i, line in enumerate(lines):
    if 'renderNew(' in line or 'renderNew()' in line:
        print(f"\n--- Found renderNew at line {i+1} ---")
        for j in range(max(0, i-2), min(len(lines), i+85)):
            print(f"{j+1}: {lines[j]}", end='')
            if 'renderCard' in lines[j] and 'join' in lines[j]:
                print(f"{j+2}: {lines[j+1]}", end='')
                break
        break

# 4. Find setNewFilter
for i, line in enumerate(lines):
    if 'setNewFilter(' in line:
        print(f"\n--- Found setNewFilter at line {i+1} ---")
        for j in range(max(0, i-2), min(len(lines), i+30)):
            print(f"{j+1}: {lines[j]}", end='')
            if 'this.renderNew()' in lines[j]:
                print(f"{j+2}: {lines[j+1]}", end='')
                break
        break

# 5. Find renderCard or where badges like PICKUP SOON or RETURN SOON are created
for i, line in enumerate(lines):
    if 'PICKUP SOON' in line or 'RETURN SOON' in line:
        print(f"\n--- Found Urgency Badges near line {i+1} ---")
        for j in range(max(0, i-10), min(len(lines), i+35)):
            print(f"{j+1}: {lines[j]}", end='')
        break
