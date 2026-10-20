with open("backend/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

line_numbers = [3015, 4094, 5174, 6202, 6487, 6800, 9659, 9697, 10622, 13351]

for ln in line_numbers:
    start = max(0, ln - 6)
    end = min(len(lines), ln + 8)
    print(f"\n--- Line {ln} ---")
    for i in range(start, end):
        print(f"{i+1}: {lines[i]}", end="")
