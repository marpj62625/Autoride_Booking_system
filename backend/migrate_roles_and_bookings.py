import psycopg
from config import SUPABASE_DB_URL

def migrate_db():
    try:
        with psycopg.connect(SUPABASE_DB_URL) as conn:
            with conn.cursor() as cur:
                print("Starting migration...")
                
                # 1. Add role column to users
                print("Adding 'role' column to 'users' table...")
                cur.execute("""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user'
                """)
                
                # 2. Add reference_num, start_time, end_time to bookings
                print("Adding new columns to 'bookings' table...")
                cur.execute("""
                    ALTER TABLE bookings 
                    ADD COLUMN IF NOT EXISTS reference_num VARCHAR(50),
                    ADD COLUMN IF NOT EXISTS start_time VARCHAR(10),
                    ADD COLUMN IF NOT EXISTS end_time VARCHAR(10)
                """)
                
                conn.commit()
                print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate_db()
