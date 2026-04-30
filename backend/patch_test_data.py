from app import app
from database import get_cursor, commit_db

def patch_data():
    with app.app_context():
        try:
            cur = get_cursor()
            email = 'autoride_tester_v4@gmail.com'
            
            # 1. Verify User
            cur.execute("UPDATE users SET is_verified=True WHERE email=%s", (email,))
            
            # 2. Get User ID
            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            user = cur.fetchone()
            if user:
                user_id = user['id']
                
                # 3. Create Sample Booking (if none exists)
                cur.execute("SELECT id FROM bookings WHERE user_id=%s", (user_id,))
                if not cur.fetchone():
                    # Get a random vehicle ID
                    cur.execute("SELECT id FROM vehicles LIMIT 1")
                    vehicle = cur.fetchone()
                    if vehicle:
                        v_id = vehicle['id']
                        cur.execute("""
                            INSERT INTO bookings (user_id, vehicle_id, total_price, status, agreed_to_terms)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING id
                        """, (user_id, v_id, 2500.00, 'Confirmed', True))
                        booking_id = cur.fetchone()['id']
                        
                        # 4. Create Payment (Safe insert - check columns first)
                        cur.execute("SELECT * FROM payments LIMIT 0")
                        pay_cols = [desc[0] for desc in cur.description]
                        
                        if 'booking_id' in pay_cols and 'amount' in pay_cols and 'status' in pay_cols:
                            cur.execute("""
                                INSERT INTO payments (booking_id, amount, status)
                                VALUES (%s, %s, %s)
                            """, (booking_id, 2500.00, 'Completed'))
                        
                        print(f"Success! User {email} verified and sample booking created.")
                else:
                    print(f"User {email} already has bookings.")
            
            commit_db()
        except Exception as e:
            print(f"Error patching data: {e}")

if __name__ == "__main__":
    patch_data()
