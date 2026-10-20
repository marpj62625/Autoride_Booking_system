import sys, os
sys.path.append(os.path.abspath('backend'))
from database import get_connection
from psycopg.rows import dict_row

conn = get_connection()
cur = conn.cursor(row_factory=dict_row)

cur.execute("""
    SELECT b.id, b.user_id, u.full_name, b.vehicle_id, v.brand, v.model, v.plate_number, v.odometer, b.start_date, b.end_date, b.status
    FROM bookings b
    JOIN users u ON b.user_id = u.id
    JOIN vehicles v ON b.vehicle_id = v.id
    WHERE b.id >= 693 AND b.id <= 705
    ORDER BY b.start_date ASC, b.id ASC
""")
rows = cur.fetchall()
print(f"Total newly allocated bookings: {len(rows)}")
for r in rows:
    print(f"ID {r['id']}: User {r['user_id']} ({r['full_name']}) | Veh {r['vehicle_id']} ({r['brand']} {r['model']} - {r['plate_number']}, Current Odo: {r['odometer']}) | {r['start_date']} to {r['end_date']} | Status: {r['status']}")

conn.close()
