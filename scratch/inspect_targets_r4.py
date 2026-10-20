with open("backend/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

def print_range(center, before=15, after=25):
    start = max(0, center - before)
    end = min(len(lines), center + after)
    print(f"=== Lines {start+1} to {end} ===")
    for i in range(start, end):
        print(f"{i+1}: {lines[i]}", end="")

print("Target 1: Line 17345 (balance_amount and quick-pricing)")
print_range(17345, 20, 25)

print("\nTarget 2: Line 2907 (admin_verify_user)")
print_range(2907, 10, 20)

print("\nTarget 3: Line 9719 (update_driver_booking_status)")
print_range(9719, 10, 20)

print("\nTarget 4: Line 10747 (get_all_support_tickets / resolve_support_ticket)")
print_range(10747, 10, 20)

print("\nTarget 5: Line 11814 (verify_user)")
print_range(11814, 10, 20)

print("\nTarget 6: Line 12955 (update_vehicle_status)")
print_range(12955, 10, 20)
