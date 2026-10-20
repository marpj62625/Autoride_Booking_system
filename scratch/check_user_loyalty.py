import sys
sys.path.insert(0, 'backend')
from app import app, get_cursor

with app.app_context():
    cur = get_cursor()

    cur.execute("""
        SELECT 
            u.id, 
            u.full_name, 
            u.email, 
            u.loyalty_points,
            u.is_regular_customer,
            u.regular_customer_manual,
            COUNT(b.id) as total_bookings,
            COUNT(CASE WHEN b.status = 'Completed' THEN 1 END) as completed_bookings,
            COALESCE(SUM(CASE WHEN b.status = 'Completed' THEN b.total_price ELSE 0 END), 0) as completed_spent,
            COALESCE(SUM(b.total_price), 0) as total_spent,
            COALESCE(SUM(CASE WHEN b.status = 'Completed' THEN b.points_earned ELSE 0 END), 0) as sum_points_earned
        FROM users u
        LEFT JOIN bookings b ON u.id = b.user_id
        WHERE u.role = 'customer'
        GROUP BY u.id, u.full_name, u.email, u.loyalty_points, u.is_regular_customer, u.regular_customer_manual
        ORDER BY u.id ASC
    """)

    users = cur.fetchall()
    print(f"Found {len(users)} customer users:\n")
    for u in users:
        print(f"ID: {u['id']:2d} | Name: {u['full_name']:25s} | DB Points: {u['loyalty_points']:3d} | Completed Spent: PHP {float(u['completed_spent']):9.2f} | Total Spent: PHP {float(u['total_spent']):9.2f} | Completed: {u['completed_bookings']:2d}/{u['total_bookings']:2d} | Bks Sum Earned: {u['sum_points_earned']}")

    print("\n--- Loyalty Settings ---")
    cur.execute("SELECT key, value, description FROM settings WHERE key LIKE '%loyalty%' OR key LIKE '%point%'")
    for s in cur.fetchall():
        print(f"{s['key']} = {s['value']} ({s['description']})")

    print("\n--- Sample Bookings for User with 0 points (e.g., Reymark Dizon Lejano) ---")
    cur.execute("""
        SELECT b.id, b.ref_code, b.total_price, b.status, b.points_earned, b.points_redeemed, b.start_date, b.end_date
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE u.full_name LIKE '%Reymark%'
        ORDER BY b.start_date ASC
    """)
    for b in cur.fetchall():
        print(b)

    print("\n--- Sample Bookings for Eliezer Cadarit Amador (DB pts: 20 vs 22k spent) ---")
    cur.execute("""
        SELECT b.id, b.ref_code, b.total_price, b.status, b.points_earned, b.points_redeemed, b.start_date, b.end_date
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE u.full_name LIKE '%Eliezer%'
        ORDER BY b.start_date ASC
    """)
    for b in cur.fetchall():
        print(b)
