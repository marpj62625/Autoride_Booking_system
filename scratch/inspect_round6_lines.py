with open("backend/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

def print_around(center, before=10, after=25):
    start = max(0, center - before)
    end = min(len(lines), center + after)
    print(f"\n=== Lines {start+1} to {end} ===")
    for i in range(start, end):
        print(f"{i+1}: {lines[i]}", end="")

print("Target 1: /admin/maintenance/export/<string:data_type>")
for idx, l in enumerate(lines):
    if "/admin/maintenance/export" in l:
        print_around(idx+1, 5, 30)
        break

print("\nTarget 2: File serving (/uploads/<path:filename>)")
for idx, l in enumerate(lines):
    if "/uploads/<path:filename>" in l or "/uploads/<filename>" in l:
        print_around(idx+1, 5, 20)
        break

print("\nTarget 3: Line 5401 (order = data.get('order'))")
print_around(5401, 10, 25)

print("\nTarget 4: Line 13813 (updates = data.get('settings', []))")
print_around(13813, 10, 25)

print("\nTarget 5: Line 9862 (chart_type)")
print_around(9862, 10, 25)
