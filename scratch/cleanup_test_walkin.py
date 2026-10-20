import sys, os
sys.path.insert(0, os.path.abspath('backend'))
from app import app, get_cursor, commit_db

with app.app_context():
    cur = get_cursor()
    cur.execute("DELETE FROM payments WHERE booking_id IN (SELECT id FROM bookings WHERE customer_name LIKE 'Test Walkin%' OR id IN (708, 709, 710))")
    cur.execute("DELETE FROM bookings WHERE customer_name LIKE 'Test Walkin%' OR id IN (708, 709, 710)")
    commit_db()
    print("Cleaned test bookings successfully!")
