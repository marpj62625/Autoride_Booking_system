import psycopg
from config import SUPABASE_DB_URL

def migrate():
    try:
        conn = psycopg.connect(SUPABASE_DB_URL)
        cur = conn.cursor()
        print("Migrating admins table...")
        cur.execute("ALTER TABLE admins ADD COLUMN IF NOT EXISTS assigned_location VARCHAR(100)")
        conn.commit()
        print("Migration complete!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
