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
           b.start_date, b.end_date, b.status, b.created_at, b.total_price
    FROM bookings b
    LEFT JOIN users u ON (b.user_id = u.id OR b.user_id = u.user_id)
    LEFT JOIN vehicles v ON b.vehicle_id = v.id
    ORDER BY b.created_at ASC
""")
bookings = cur.fetchall()
print(f"Total bookings: {len(bookings)}")
for b in bookings:
    print(dict(b))

cur.close()
conn.close()
