from app import app
from database import get_cursor

def verify_system_health():
    print("--- AUTORIDE SYSTEM COMPREHENSIVE TEST ---")
    
    with app.app_context():
        try:
            cur = get_cursor()
            
            # 1. IDENTIFY SCHEMA (Check columns)
            cur.execute("SELECT * FROM bookings LIMIT 0")
            columns = [desc[0] for desc in cur.description]
            print(f"[SCHEMA] Bookings columns: {columns}")
            
            # 2. CHECK TEST USER (@gmail restriction proof)
            email = 'autoride_tester_v4@gmail.com'
            cur.execute("SELECT id, full_name, is_verified FROM users WHERE email=%s", (email,))
            user = cur.fetchone()
            if user:
                v_status = "VERIFIED" if user['is_verified'] == 1 else "PENDING VERIFICATION"
                print(f"[USER] {user['full_name']} ({email}) -> status: {v_status}")
                user_id = user['id']
                
                # 3. CHECK RECENT BOOKINGS
                # We skip 'created_at' as it might not exist
                cur.execute("SELECT id, vehicle_id, total_price, status FROM bookings WHERE user_id=%s ORDER BY id DESC LIMIT 1", (user_id,))
                booking = cur.fetchone()
                if booking:
                    print(f"[BOOKING] ID: {booking['id']}, Status: {booking['status']}, Total: PHP {booking['total_price']}")
                    
                    # 4. CHECK PAYMENTS
                    cur.execute("SELECT id, amount, status FROM payments WHERE booking_id=%s", (booking['id'],))
                    payment = cur.fetchone()
                    if payment:
                        print(f"[PAYMENT] ID: {payment['id']}, Amount: PHP {payment['amount']}, Status: {payment['status']}")
                    else:
                        print("[PAYMENT] FAIL: No payment record found for this booking.")
                else:
                    print("[BOOKING] FAIL: No bookings found for the test user.")
            else:
                print(f"[USER] FAIL: Test user {email} not found.")

            # 5. ADMIN REPORT ENGINE TEST (Top 5 Vehicles)
            print("\n--- ADMIN REPORTS ENGINE TEST ---")
            # We cast total_price to decimal to handle potential string/numeric types safely
            query = """
                SELECT v.name, COUNT(b.id) as booking_count, SUM(cast(b.total_price as decimal)) as total_revenue
                FROM bookings b
                JOIN vehicles v ON b.vehicle_id = v.id
                WHERE b.status IN ('Confirmed', 'Completed')
                GROUP BY v.id, v.name
                ORDER BY booking_count DESC
                LIMIT 5
            """
            cur.execute(query)
            top_vehicles = cur.fetchall()
            if top_vehicles:
                for v in top_vehicles:
                    rev = f"{v['total_revenue']:.2f}" if v['total_revenue'] else "0.00"
                    print(f"Vehicle: {v['name']} | Bookings: {v['booking_count']} | Revenue: PHP {rev}")
            else:
                print("WAIT: No confirmed/completed bookings found for reports yet.")

        except Exception as e:
            print(f"TEST ERROR: {str(e)}")
        finally:
            print("--- TEST COMPLETE ---")

if __name__ == "__main__":
    verify_system_health()
