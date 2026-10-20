with open("backend/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

def print_around(center, before=8, after=18):
    start = max(0, center - before)
    end = min(len(lines), center + after)
    print(f"\n=== Lines {start+1} to {end} ===")
    for i in range(start, end):
        print(f"{i+1}: {lines[i]}", end="")

print("Target 1: Lines 8684 & 8902 (strptime in cancel penalty)")
print_around(8684, 8, 15)
print_around(8902, 8, 15)

print("\nTarget 2: Line 6140 (user_id in user bookings)")
print_around(6140, 5, 15)

print("\nTarget 3: Line 11027 (user_id in notifications)")
print_around(11027, 5, 15)

print("\nTarget 4: Line 14073 (page/limit in activity logs)")
print_around(14073, 5, 15)

print("\nTarget 5: Line 16296 (user_id / admin_id in chat history)")
print_around(16296, 5, 15)
