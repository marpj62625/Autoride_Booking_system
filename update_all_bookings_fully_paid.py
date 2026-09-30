import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from config import SUPABASE_DB_URL
import psycopg2
from psycopg2.extras import RealDictCursor

def main():
    conn = psycopg2.connect(SUPABASE_DB_URL)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        print("=== Step 1: Updating All 16 Bookings to Fully Paid (Paid) ===")
        # Fetch all bookings
        cur.execute("SELECT id, booking_id, user_id, total_price, amount_paid, balance_amount, status, payment_status, points_earned FROM bookings ORDER BY id")
        bookings = cur.fetchall()

        for b in bookings:
            bid = b['id'] or b['booking_id']
            tot = float(b['total_price'])
            uid = b['user_id']
            pts = int(b.get('points_earned') or 0)

            # Update booking to Paid / balance 0
            cur.execute("""
                UPDATE bookings
                SET payment_status = 'Paid',
                    amount_paid = %s,
                    balance_amount = 0.00
                WHERE id = %s
            """, (tot, bid))

            # Check existing payments for this booking
            cur.execute("SELECT payment_id, amount FROM payments WHERE booking_id = %s", (bid,))
            pmts = cur.fetchall()
            existing_paid = sum(float(p['amount']) for p in pmts)

            if existing_paid < tot:
                diff = tot - existing_paid
                ref = f"PAY-FULL-{bid}-{int(diff)}"
                cur.execute("""
                    INSERT INTO payments (booking_id, amount, method, reference_number, status)
                    VALUES (%s, %s, 'GCash', %s, 'completed')
                """, (bid, diff, ref))
                print(f"Booking #{bid} (User {uid}): Added remaining payment of PHP {diff:,.2f} (Total: PHP {tot:,.2f})")
            else:
                print(f"Booking #{bid} (User {uid}): Already had full payment of PHP {existing_paid:,.2f}")

        # Step 2: Ensure loyalty points are credited for all completed/paid bookings
        print("\n=== Step 2: Crediting Loyalty Points for All Paid Bookings ===")
        # Reset and accurately calculate each user's loyalty points from all their paid bookings
        cur.execute("""
            UPDATE users u
            SET loyalty_points = COALESCE((
                SELECT SUM(b.points_earned)
                FROM bookings b
                WHERE b.user_id = u.id AND b.payment_status IN ('Paid', 'Fully Paid')
            ), 0)
            WHERE u.role = 'customer'
        """)

        conn.commit()
        print("\nAll bookings updated to Paid and points synchronized successfully!")

        # Step 3: Verify stats
        print("\n=== Step 3: Verifying Database Totals ===")
        cur.execute("""
            SELECT 
                COUNT(*) as total_bookings,
                SUM(total_price) as total_price_sum,
                SUM(amount_paid) as total_paid_sum,
                SUM(balance_amount) as total_balance_sum
            FROM bookings
            WHERE payment_status IN ('Paid', 'Fully Paid')
        """)
        totals = cur.fetchone()
        print(f"Total Paid Bookings: {totals['total_bookings']}")
        print(f"Total Revenue: PHP {float(totals['total_paid_sum']):,.2f}")
        print(f"Total Outstanding Balance: PHP {float(totals['total_balance_sum']):,.2f}")

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()
