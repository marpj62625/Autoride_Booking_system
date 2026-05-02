import psycopg
from config import SUPABASE_DB_URL

def debug_user_data():
    email = "testcompany0626@gmail.com"
    try:
        conn = psycopg.connect(SUPABASE_DB_URL)
        cursor = conn.cursor()
        
        # 1. Check User Status
        cursor.execute("SELECT id, full_name, email, is_verified, is_email_verified FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"ERROR: User with email {email} NOT FOUND in database.")
            return

        user_id = user[0]
        print(f"USER FOUND: ID={user_id}, Name={user[1]}, Verified={user[3]}, EmailVerified={user[4]}")

        # 2. Check Bookings
        cursor.execute("SELECT id, vehicle_id, start_date, end_date, status, payment_status FROM bookings WHERE user_id = %s ORDER BY id DESC", (user_id,))
        bookings = cursor.fetchall()
        
        print(f"\nFOUND {len(bookings)} BOOKINGS for this user:")
        for b in bookings:
            print(f"  - ID: {b[0]}, Vehicle: {b[1]}, Dates: {b[2]} to {b[3]}, Status: {b[4]}, Payment: {b[5]}")

        # 3. Check Vehicles (to see if they exist)
        if bookings:
            v_ids = tuple(set([b[1] for b in bookings]))
            if len(v_ids) == 1:
                cursor.execute(f"SELECT id, brand, model FROM vehicles WHERE id = {v_ids[0]}")
            else:
                cursor.execute(f"SELECT id, brand, model FROM vehicles WHERE id IN {v_ids}")
            vehicles = cursor.fetchall()
            print(f"\nVEHICLE DATA FOR THESE BOOKINGS:")
            for v in vehicles:
                print(f"  - ID: {v[0]}, Name: {v[1]} {v[2]}")

        conn.close()
    except Exception as e:
        print(f"DB DEBUG ERROR: {e}")

if __name__ == "__main__":
    debug_user_data()
