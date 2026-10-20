import sys, os
sys.path.append(os.path.abspath('backend'))
from database import get_connection
from psycopg.rows import dict_row

conn = get_connection()
cur = conn.cursor(row_factory=dict_row)

user_ids = [25, 26, 27, 28, 29, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]
for uid in user_ids:
    cur.execute("SELECT full_name, phone, email FROM users WHERE id = %s", (uid,))
    u = cur.fetchone()
    cur.execute("SELECT id, vehicle_id, start_date, end_date FROM bookings WHERE user_id = %s AND end_date >= '2026-09-01' ORDER BY start_date ASC", (uid,))
    bks = cur.fetchall()
    bk_str = ', '.join([f"{b['start_date']}->{b['end_date']} (veh {b['vehicle_id']})" for b in bks])
    print(f"User #{uid}: {u['full_name']} | Total: {len(bks)} bookings | [{bk_str}]")

conn.close()
