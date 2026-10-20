import sys
sys.path.insert(0, 'backend')
from app import app, get_cursor, commit_db

with app.app_context():
    cur = get_cursor()

    print("--- 1. Recalculating points_earned for Completed bookings ---")
    cur.execute("""
        SELECT id, user_id, total_price, points_earned, status
        FROM bookings
        WHERE LOWER(status) = 'completed'
        ORDER BY id ASC
    """)
    completed_bks = cur.fetchall()

    updated_bks_count = 0
    for b in completed_bks:
        expected_pts = int(float(b['total_price'] or 0) / 100)
        curr_pts = int(b.get('points_earned') or 0)
        if curr_pts != expected_pts:
            cur.execute("UPDATE bookings SET points_earned = %s WHERE id = %s", (expected_pts, b['id']))
            updated_bks_count += 1
            print(f"  Booking #{b['id']} (User #{b['user_id']}): PHP {float(b['total_price']):,.2f} -> points_earned updated from {curr_pts} to {expected_pts}")

    print(f"Total bookings updated: {updated_bks_count}\n")

    print("--- 2. Syncing users loyalty_points from Completed bookings ---")
    cur.execute("SELECT id, full_name, loyalty_points FROM users WHERE role = 'customer' ORDER BY id ASC")
    customers = cur.fetchall()

    for c in customers:
        u_id = c['id']
        # Calculate total earned from completed bookings
        cur.execute("""
            SELECT 
                COALESCE(SUM(points_earned), 0) as total_earned,
                COALESCE(SUM(points_redeemed), 0) as total_redeemed,
                COALESCE(SUM(total_price), 0) as completed_spent,
                COUNT(id) as completed_count
            FROM bookings
            WHERE user_id = %s AND LOWER(status) = 'completed'
        """, (u_id,))
        stats = cur.fetchone()

        earned = int(stats['total_earned'] or 0)
        redeemed = int(stats['total_redeemed'] or 0)
        net_points = max(0, earned - redeemed)
        old_points = int(c['loyalty_points'] or 0)

        cur.execute("UPDATE users SET loyalty_points = %s WHERE id = %s", (net_points, u_id))
        diff_str = f"(+{net_points - old_points})" if net_points > old_points else f"({net_points - old_points})" if net_points < old_points else "(unchanged)"
        print(f"User #{u_id:2d} | {c['full_name']:25s} | Old Pts: {old_points:3d} -> New Pts: {net_points:3d} {diff_str:11s} | Completed Spent: PHP {float(stats['completed_spent']):,.2f} ({stats['completed_count']} bks)")

    commit_db()
    print("\n[SUCCESS] All loyalty points and bookings successfully synced and committed!")
