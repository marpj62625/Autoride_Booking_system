import sys
sys.path.insert(0, 'backend')
from app import app, get_cursor

with app.app_context():
    cur = get_cursor()
    cur.execute("""
        SELECT 
            COUNT(*) as total_completed,
            COUNT(CASE WHEN start_date < '2026-09-14' THEN 1 END) as before_sep14,
            COUNT(CASE WHEN start_date >= '2026-09-14' THEN 1 END) as sep14_onwards
        FROM bookings
        WHERE status = 'Completed'
    """)
    counts = cur.fetchone()
    print("--- COUNTS ---")
    print(f"Total Completed: {counts['total_completed']}")
    print(f"Before Sep 14, 2026: {counts['before_sep14']}")
    print(f"From Sep 14, 2026 onwards: {counts['sep14_onwards']}")

    print("\n--- Completed Bookings from Sep 14, 2026 onwards ---")
    cur.execute("""
        SELECT b.id, b.user_id, u.full_name, b.start_date, b.end_date, b.total_price, v.brand, v.model
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        LEFT JOIN vehicles v ON b.vehicle_id = v.id
        WHERE b.status = 'Completed' AND b.start_date >= '2026-09-14'
        ORDER BY b.start_date ASC
    """)
    for b in cur.fetchall():
        print(f"  Booking #{b['id']:3d} | User #{b['user_id']:2d} ({b['full_name'][:20]:20s}) | Dates: {b['start_date']} to {b['end_date']} | PHP {float(b['total_price']):,.2f} | {b['brand']} {b['model']}")

    print("\n--- Completed Bookings before Sep 14, 2026 (Historical) ---")
    cur.execute("""
        SELECT b.id, b.user_id, u.full_name, b.start_date, b.end_date, b.total_price, v.brand, v.model
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        LEFT JOIN vehicles v ON b.vehicle_id = v.id
        WHERE b.status = 'Completed' AND b.start_date < '2026-09-14'
        ORDER BY b.start_date ASC
    """)
    b_before = cur.fetchall()
    print(f"Count: {len(b_before)} bookings (from {b_before[0]['start_date']} to {b_before[-1]['start_date']})")
