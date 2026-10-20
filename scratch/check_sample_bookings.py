import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
from app import app, get_cursor

with app.app_context():
    cur = get_cursor()
    cur.execute("SELECT id, booking_id, customer_name, user_id, status FROM bookings ORDER BY id DESC LIMIT 5")
    rows = cur.fetchall()
    print("Recent bookings sample:")
    for r in rows:
        print(f"  id={r['id']}, booking_id={r['booking_id']}, user_id={r['user_id']}, name={r['customer_name']}, status={r['status']}")
