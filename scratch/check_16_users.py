import sys, psycopg
sys.path.insert(0, 'AutorideSystem/backend')
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row

conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)

user_ids = [25, 26, 27, 28, 29, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]

cur.execute("""
    SELECT b.id, b.user_id, u.full_name as user_name, u.email,
           b.vehicle_id, v.brand, v.model, v.plate_number,
           b.start_date, b.end_date, b.total_price, b.status,
           b.payment_type, b.payment_status, b.amount_paid, b.balance_amount,
           b.points_earned
    FROM bookings b
    JOIN users u ON b.user_id = u.id
    JOIN vehicles v ON b.vehicle_id = v.id
    WHERE b.user_id = ANY(%s) AND b.start_date >= '2026-09-01'
    ORDER BY b.start_date ASC, b.id ASC
""", (user_ids,))

rows = cur.fetchall()
print(f"Total bookings found for 16 official users (Sept 2026 onwards): {len(rows)}")
for r in rows:
    print(f"Booking #{r['id']} | User #{r['user_id']} ({r['user_name']}) | {r['brand']} {r['model']} ({r['plate_number']}) | {r['start_date']} to {r['end_date']} | Status: {r['status']} | Paid: {r['amount_paid']} | Balance: {r['balance_amount']} | Points: {r['points_earned']}")

# Also check users verification and status
cur.execute("""
    SELECT id, full_name, email, is_verified, is_regular_customer, loyalty_points
    FROM users
    WHERE id = ANY(%s)
    ORDER BY id ASC
""", (user_ids,))
users = cur.fetchall()
print(f"\nUser Verification & Account Status ({len(users)} users):")
for u in users:
    print(f"User #{u['id']}: {u['full_name']} | Verified: {u['is_verified']} | VIP/Regular: {u['is_regular_customer']} | Points: {u['loyalty_points']}")

conn.close()
