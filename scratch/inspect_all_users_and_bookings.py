import sys
sys.path.append('backend')
import psycopg
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row

conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)

cur.execute("""
    SELECT u.id, u.user_id, u.full_name, u.email, u.phone, u.created_at,
           ld.license_number, ld.created_at as license_created_at
    FROM users u
    LEFT JOIN license_details ld ON (u.id = ld.user_id OR u.user_id = ld.user_id)
    WHERE u.role = 'customer' OR u.role IS NULL
    ORDER BY u.id
""")
users = cur.fetchall()
print(f"Total customers: {len(users)}")
for u in users:
    print(f"ID={u['id']}/UID={u['user_id']} | {u['full_name']} | Registered: {u['created_at']} | License: {u['license_number']} (Uploaded: {u['license_created_at']})")

print("\n--- ALL BOOKINGS ---")
cur.execute("""
    SELECT b.id, b.booking_id, b.user_id, u.full_name, v.brand, v.model, 
           b.start_date, b.end_date, b.start_time, b.end_time,
           b.status, b.created_at, b.total_price
    FROM bookings b
    LEFT JOIN users u ON (b.user_id = u.id OR b.user_id = u.user_id)
    LEFT JOIN vehicles v ON b.vehicle_id = v.id
    ORDER BY b.created_at ASC
""")
bookings = cur.fetchall()
print(f"Total bookings: {len(bookings)}")
for b in bookings:
    print(f"Booking #{b['booking_id']} (ID={b['id']}) | User {b['user_id']} ({b['full_name']}) | Vehicle: {b['brand']} {b['model']} | Dates: {b['start_date']} to {b['end_date']} | Created: {b['created_at']} | Status: {b['status']}")

cur.close()
conn.close()
