import sys
sys.path.insert(0, 'backend')
from app import app, get_cursor

with app.app_context():
    cur = get_cursor()
    cur.execute("""
        SELECT id, customer_name, user_id, start_date, end_date
        FROM bookings
        WHERE id >= 414 AND id <= 435
        ORDER BY id ASC
    """)
    for b in cur.fetchall():
        uid_str = str(b['user_id']) if b['user_id'] else "NULL"
        print(f"Booking #{b['id']:3d} | user_id: {uid_str:5s} | Customer: {b['customer_name']} | Dates: {b['start_date']} to {b['end_date']}")
