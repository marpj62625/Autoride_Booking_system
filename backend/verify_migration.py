import psycopg
from config import SUPABASE_DB_URL

def verify_migration():
    try:
        conn = psycopg.connect(SUPABASE_DB_URL)
        cur = conn.cursor()
        
        # Check columns of users table
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users'
            AND column_name IN ('is_email_verified', 'is_driver', 'is_verified')
        """)
        columns = cur.fetchall()
        print("\n--- User Table Verification ---")
        for col in columns:
            print(f"Column: {col[0]}, Type: {col[1]}")
            
        # Check if synchronization worked for verified users
        cur.execute("SELECT COUNT(*) FROM users WHERE is_verified = TRUE AND is_email_verified = FALSE")
        unsynced = cur.fetchone()[0]
        print(f"Unsynced verified users: {unsynced}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_migration()
