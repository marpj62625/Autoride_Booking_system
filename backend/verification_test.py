import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = 'postgresql://postgres.fydfsgjrlowrrtlmefwq:Autoride777%25*@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres'

def find_pending_user():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("Searching for users with pending license verification...")
        cur.execute("""
            SELECT id, full_name, email, is_verified, is_email_verified 
            FROM users 
            WHERE license_image IS NOT NULL AND is_verified = 0 
            LIMIT 1
        """)
        user = cur.fetchone()
        
        if user:
            print(f"FOUND CANDIDATE:")
            print(f"ID: {user['id']}")
            print(f"Name: {user['full_name']}")
            print(f"Email: {user['email']}")
            print(f"Email Verified: {user['is_email_verified']}")
            print(f"License Status: {user['is_verified']} (Pending)")
        else:
            print("No pending users with license images found.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    find_pending_user()
