from app import app
from database import get_cursor

def get_final_ref():
    with app.app_context():
        try:
            cur = get_cursor()
            email = 'patrickciar78@gmail.com'
            cur.execute("SELECT reference_number FROM bookings WHERE user_id = (SELECT id FROM users WHERE email=%s) ORDER BY created_at DESC LIMIT 1", (email,))
            ref = cur.fetchone()
            if ref:
                print(ref[0])
            else:
                print("No booking ref found")
            cur.close()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    get_final_ref()
