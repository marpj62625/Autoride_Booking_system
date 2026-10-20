import sys
sys.path.append('backend')
from database import get_connection
from psycopg.rows import dict_row

conn = get_connection()
cur = conn.cursor(row_factory=dict_row)

# 1. Bookings created today (or within the last 24 hours / since Oct 12 evening)
cur.execute("""
    SELECT id, user_id, vehicle_id, customer_name, customer_phone, start_date, end_date, total_price, status, created_at
    FROM bookings
    WHERE created_at >= NOW() - INTERVAL '24 hours'
    ORDER BY id ASC
""")
bookings = cur.fetchall()

print(f"=== BOOKINGS CREATED IN THE LAST 24 HOURS (Total: {len(bookings)}) ===")
for b in bookings:
    print(f"ID: {b['id']} | User: {b['user_id']} | Cust: {b['customer_name']} | Phone: {b['customer_phone']} | Dates: {b['start_date']} -> {b['end_date']} | Created: {b['created_at']}")

# 2. Users created today (or within last 24 hours)
cur.execute("""
    SELECT id, first_name, last_name, full_name, email, phone, role, is_verified, created_at
    FROM users
    WHERE created_at >= NOW() - INTERVAL '24 hours'
    ORDER BY id ASC
""")
users = cur.fetchall()

print(f"\n=== USERS CREATED IN THE LAST 24 HOURS (Total: {len(users)}) ===")
for u in users:
    print(f"ID: {u['id']} | Name: {u['full_name']} | Email: {u['email']} | Phone: {u['phone']} | Role: {u['role']} | Verified: {u['is_verified']} | Created: {u['created_at']}")

# Also show the very latest 30 bookings regardless of date just to see the latest IDs
cur.execute("""
    SELECT id, user_id, vehicle_id, customer_name, start_date, end_date, status, created_at
    FROM bookings
    ORDER BY id DESC
    LIMIT 30
""")
latest_bks = cur.fetchall()
print(f"\n=== LATEST 30 BOOKINGS IN DATABASE ===")
for b in latest_bks:
    print(f"ID: {b['id']} | User: {b['user_id']} | Cust: {b['customer_name']} | Dates: {b['start_date']} -> {b['end_date']} | Created: {b['created_at']}")

conn.close()
