with open("backend/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

def print_fn_around(center, n_before=10, n_after=30):
    start = max(0, center - n_before)
    end = min(len(lines), center + n_after)
    print(f"=== Lines {start+1} to {end} ===")
    for i in range(start, end):
        print(f"{i+1}: {lines[i]}", end="")

print("Target 1: Line 6519 (rating / review)")
print_fn_around(6519, 10, 30)

print("\nTarget 2: Line 6283 (phone in profile update)")
print_fn_around(6283, 10, 25)

print("\nTarget 3: Line 7423 (customer_phone and emergency_phone)")
print_fn_around(7423, 10, 30)
