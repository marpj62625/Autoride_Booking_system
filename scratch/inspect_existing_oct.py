import sys, os
sys.path.append(os.path.abspath('backend'))
from database import get_connection
from psycopg.rows import dict_row

conn = get_connection()
cur = conn.cursor(row_factory=dict_row)

user_ids = [25, 26, 27, 28, 29, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]

# 1. Fetch the 16 users
cur.execute("SELECT id, full_name, email, phone FROM users WHERE id = ANY(%s) ORDER BY id ASC", (user_ids,))
users = {u['id']: u for u in cur.fetchall()}

# 2. Fetch all bookings for these 16 users from Sept 1, 2026 onwards
cur.execute("""
    SELECT b.id, b.user_id, u.full_name as user_name, b.vehicle_id, v.brand, v.model, v.plate_number,
           b.start_date, b.end_date, b.status
    FROM bookings b
    JOIN users u ON b.user_id = u.id
    JOIN vehicles v ON b.vehicle_id = v.id
    WHERE b.user_id = ANY(%s) AND b.end_date >= '2026-09-01'
    ORDER BY b.start_date ASC, b.id ASC
""", (user_ids,))
user_bookings = cur.fetchall()

print(f"=== CURRENT BOOKINGS FOR THE 16 USERS (Sept 2026 Onwards) ===")
print(f"Total bookings: {len(user_bookings)}")
for b in user_bookings:
    print(f"User #{b['user_id']} ({b['user_name']}) | {b['brand']} {b['model']} [{b['plate_number']}] | {b['start_date']} -> {b['end_date']} | Status: {b['status']}")

# 3. Fetch all bookings in general from Oct 1, 2026 onwards across all vehicles
cur.execute("""
    SELECT b.id, b.user_id, b.customer_name, b.vehicle_id, v.brand, v.model, v.plate_number,
           b.start_date, b.end_date, b.status
    FROM bookings b
    LEFT JOIN vehicles v ON b.vehicle_id = v.id
    WHERE b.end_date >= '2026-10-01'
    ORDER BY b.start_date ASC, b.id ASC
""")
all_oct_bookings = cur.fetchall()
print(f"\n=== ALL CURRENT BOOKINGS IN DB FROM OCT 2026 ONWARDS (Total: {len(all_oct_bookings)}) ===")
for b in all_oct_bookings:
    print(f"ID #{b['id']} | User: {b['user_id']} | Cust: {b['customer_name']} | Veh: {b['brand']} {b['model']} [{b['plate_number']}] | {b['start_date']} -> {b['end_date']} | Status: {b['status']}")

conn.close()
