import sys
sys.path.insert(0, 'backend')
from app import app, get_cursor

with app.app_context():
    cur = get_cursor()

    cur.execute("""
        SELECT 
            b.id,
            b.user_id,
            u.full_name,
            b.reference_num,
            b.total_price,
            b.status,
            b.points_earned,
            b.points_redeemed,
            b.start_date,
            b.end_date,
            b.created_at
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE u.id IN (38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48)
        ORDER BY b.user_id ASC, b.start_date ASC
    """)

    bookings = cur.fetchall()
    print(f"Total bookings for new users: {len(bookings)}\n")
    current_uid = None
    for b in bookings:
        if b['user_id'] != current_uid:
            current_uid = b['user_id']
            print(f"\n--- User #{b['user_id']}: {b['full_name']} ---")
        print(f"  Booking #{b['id']} ({b['reference_num']}) | Dates: {b['start_date']} to {b['end_date']} | Status: {b['status']:10s} | Total: PHP {float(b['total_price']):,.2f} | Pts Earned: {b['points_earned']} | Pts Redeemed: {b['points_redeemed']}")
