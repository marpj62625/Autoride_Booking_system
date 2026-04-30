from app import app
from database import get_cursor

def check_results():
    print("--- AUTORIDE SYSTEM TEST REPORT ---")
    
    with app.app_context():
        try:
            cur = get_cursor()
            
            # 1. Check User Verification Status
            email = 'autoride_tester_v4@gmail.com'
            cur.execute("SELECT id, full_name, is_verified FROM users WHERE email=%s", (email,))
            user = cur.fetchone()
            if user:
                v_status = "VERIFIED" if user['is_verified'] == 1 else "NOT VERIFIED"
                print(f"User: {user['full_name']} ({email})")
                print(f"Verification Status: {v_status}")
                user_id = user['id']
                
                # 2. Check Bookings
                cur.execute("""
                    SELECT b.id, v.name as vehicle, b.total_price, b.status, b.created_at 
                    FROM bookings b 
                    JOIN vehicles v ON b.vehicle_id = v.id 
                    WHERE b.user_id = %s 
                    ORDER BY b.id DESC LIMIT 1
                """, (user_id,))
                booking = cur.fetchone()
                if booking:
                    print(f"\nLast Booking Found:")
                    print(f"  ID: {booking['id']}")
                    print(f"  Vehicle: {booking['vehicle']}")
                    print(f"  Total: PHP {booking['total_price']}")
                    print(f"  Status: {booking['status']}")
                    print(f"  Date: {booking['created_at']}")
                    
                    # 3. Check Payments
                    cur.execute("SELECT id, amount, status FROM payments WHERE booking_id = %s", (booking['id'],))
                    payment = cur.fetchone()
                    if payment:
                        print(f"\nPayment Found:")
                        print(f"  ID: {payment['id']}")
                        print(f"  Amount: PHP {payment['amount']}")
                        print(f"  Status: {payment['status']}")
                    else:
                        print("\nNo payment found for this booking yet.")
                else:
                    print("\nNo bookings found for this user.")
            else:
                print(f"\nUser {email} not found in database.")
                
        except Exception as e:
            print(f"Error checking results: {str(e)}")
        finally:
            print("\n-----------------------------------------")

if __name__ == "__main__":
    check_results()
