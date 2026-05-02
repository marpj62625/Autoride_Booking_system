import psycopg
import os
from dotenv import load_dotenv

# Path to the .env file in the backend directory
env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
load_dotenv(env_path)

DB_URL = "postgresql://postgres.fydfsgjrlowrrtlmefwq:Autoride777%25*@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

def fix_admin():
    print(f"Connecting to: {DB_URL}")
    try:
        with psycopg.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                # Update the admin account to be verified and have the right role
                cur.execute("""
                    UPDATE users 
                    SET is_verified = 1, role = 'super_admin' 
                    WHERE email = 'superadmin@autoride.com'
                """)
                if cur.rowcount == 0:
                    print("Admin not found! Creating new superadmin...")
                    cur.execute("""
                        INSERT INTO users (full_name, email, password, role, is_verified, is_email_verified)
                        VALUES ('Super Admin', 'superadmin@autoride.com', 'admin12345', 'super_admin', 1, True)
                    """)
                conn.commit()
                print("Admin account successfully fixed/created!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_admin()
