
import psycopg
from config import SUPABASE_DB_URL

def check_users():
    try:
        conn = psycopg.connect(SUPABASE_DB_URL)
        with conn.cursor() as cur:
            cur.execute("SELECT id, full_name, email, is_driver, is_email_verified FROM users")
            users = cur.fetchall()
            print(f"{'ID':<5} | {'Name':<20} | {'Email':<30} | {'Driver':<6} | {'Verified':<8}")
            print("-" * 80)
            for user in users:
                print(f"{user[0]:<5} | {str(user[1]):<20} | {str(user[2]):<30} | {str(user[3]):<6} | {str(user[4]):<8}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    check_users()
