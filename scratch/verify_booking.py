from app import app
from database import get_cursor

with app.app_context():
    cur = get_cursor()
    # Get user ID
    cur.execute("SELECT id FROM users WHERE email='patrickciar78@gmail.com'")
    user = cur.fetchone()
    if not user:
        print("User not found")
    else:
        user_id = user[0]
        # Get latest booking
        cur.execute("""
            SELECT b.id, b.reference_number, b.total_price, b.status, v.brand, v.model, b.created_at
            FROM bookings b
            JOIN vehicles v ON b.vehicle_id = v.id
            WHERE b.user_id = %s
            ORDER BY b.created_at DESC
            LIMIT 1
        """, (user_id,))
        booking = cur.fetchone()
        if booking:
            booking_dict = {
                'id': booking[0],
                'reference_number': booking[1],
                'total_price': float(booking[2]),
                'status': booking[3],
                'vehicle': f"{booking[4]} {booking[5]}",
                'created_at': str(booking[6])
            }
            print(booking_dict)
        else:
            print("No booking found")
    cur.close()
