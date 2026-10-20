import sys
sys.path.append('backend')
import psycopg
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row

conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)

cur.execute("""
    SELECT b.id, b.booking_id, b.user_id, 
           COALESCE(u.full_name, b.customer_name) as customer_name,
           v.brand, v.model,
           b.start_date, b.end_date, b.status, b.created_at, b.total_price, b.cancellation_reason
    FROM bookings b
    LEFT JOIN users u ON (b.user_id = u.id OR b.user_id = u.user_id)
    LEFT JOIN vehicles v ON b.vehicle_id = v.id
    WHERE b.start_date >= '2026-09-14'
    ORDER BY b.start_date ASC, b.id ASC
""")
rows = cur.fetchall()
print(f"Total user/recent bookings: {len(rows)}")
for r in rows:
    print(f"#{r['booking_id']} | User {r['user_id']} ({r['customer_name']}) | {r['brand']} {r['model']} | {r['start_date']} to {r['end_date']} | Created: {r['created_at']} | Status: {r['status']}")

cur.close()
conn.close()
