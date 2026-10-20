import sys
sys.path.append('backend')
import psycopg
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row

conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)

print("--- ADMIN USERS ---")
cur.execute("SELECT id, user_id, full_name, email, role FROM users WHERE role IN ('admin', 'super_admin')")
admins = cur.fetchall()
for a in admins:
    print(dict(a))

print("\n--- CURRENT NOTIFICATIONS ---")
cur.execute("SELECT COUNT(*) as total FROM notifications")
print("Total notifications in DB:", cur.fetchone()['total'])

cur.execute("SELECT COUNT(*) as admin_notifs FROM notifications WHERE type LIKE 'admin_%'")
print("Admin notifications (type LIKE 'admin_%'):", cur.fetchone()['admin_notifs'])

cur.execute("SELECT id, user_id, title, message, type, is_read, created_at FROM notifications WHERE type LIKE 'admin_%' ORDER BY created_at DESC LIMIT 10")
for r in cur.fetchall():
    print(dict(r))

print("\n--- CUSTOMER USERS ---")
cur.execute("SELECT id, user_id, full_name, email, phone, is_verified, license_status, created_at FROM users WHERE role = 'customer' OR role IS NULL LIMIT 25")
customers = cur.fetchall()
print(f"Total customers sampled: {len(customers)}")
for c in customers[:5]:
    print(dict(c))

print("\n--- BOOKINGS SAMPLE ---")
cur.execute("""
    SELECT b.id, b.booking_id, b.user_id, u.full_name, v.brand, v.model, b.start_date, b.end_date, b.status, b.created_at, b.total_price
    FROM bookings b
    LEFT JOIN users u ON b.user_id = u.id OR b.user_id = u.user_id
    LEFT JOIN vehicles v ON b.vehicle_id = v.id
    ORDER BY b.created_at DESC
    LIMIT 20
""")
bookings = cur.fetchall()
print(f"Bookings sampled: {len(bookings)}")
for b in bookings[:10]:
    print(dict(b))

cur.close()
conn.close()
