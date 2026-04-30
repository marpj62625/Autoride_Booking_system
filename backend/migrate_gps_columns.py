import psycopg
from config import SUPABASE_DB_URL

def migrate():
    conn = None
    try:
        conn = psycopg.connect(SUPABASE_DB_URL)
        cursor = conn.cursor()

        print("Adding GPS columns to vehicles table...")
        cursor.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 8)")
        cursor.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS longitude DECIMAL(11, 8)")
        cursor.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS last_gps_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        conn.commit()
        print("Migration successful: GPS columns added.")

    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    migrate()
