from app import app
from database import get_cursor
import json

with app.app_context():
    try:
        cur = get_cursor()
        cur.execute("SELECT COUNT(*) AS total FROM bookings")
        total = cur.fetchone()['total']
        print(f"Total Bookings: {total}")

        cur.execute("SELECT start_date, total_price FROM bookings ORDER BY start_date DESC LIMIT 5")
        rows = cur.fetchall()
        print("Recent Bookings:")
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error: {e}")
