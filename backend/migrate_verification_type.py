import psycopg2
from config import SUPABASE_DB_URL

def migrate():
    conn = None
    try:
        print(f"Connecting to database...")
        conn = psycopg2.connect(SUPABASE_DB_URL)
        cur = conn.cursor()
        
        print("Starting migration of users.is_verified column...")
        
        # 1. Drop existing default first
        cur.execute("ALTER TABLE users ALTER COLUMN is_verified DROP DEFAULT;")
        
        # 2. Alter type with USING clause to map BOOLEAN -> INTEGER
        cur.execute("""
            ALTER TABLE users 
            ALTER COLUMN is_verified TYPE INTEGER 
            USING (CASE WHEN is_verified THEN 1 ELSE 0 END);
        """)
        
        # 3. Set default value to 0 (Pending)
        cur.execute("ALTER TABLE users ALTER COLUMN is_verified SET DEFAULT 0;")
        
        conn.commit()
        print("MIGRATION SUCCESSFUL: users.is_verified is now INTEGER.")
        
        # Verify
        cur.execute("SELECT id, full_name, is_verified FROM users LIMIT 5")
        rows = cur.fetchall()
        print("\nVerification (First 5 users):")
        for r in rows:
            print(f"ID: {r[0]} | Name: {r[1]} | Status: {r[2]}")
            
    except Exception as e:
        print(f"MIGRATION FAILED: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == '__main__':
    migrate()
