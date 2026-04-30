import psycopg
from config import SUPABASE_DB_URL

def check():
    try:
        with psycopg.connect(SUPABASE_DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='vehicle_images' AND column_name='order_index';")
                res = cur.fetchone()
                if res:
                    print("COLUMN_EXISTS")
                else:
                    print("COLUMN_MISSING")
                    # Try to add it here
                    cur.execute("ALTER TABLE vehicle_images ADD COLUMN order_index INTEGER DEFAULT 0;")
                    conn.commit()
                    print("COLUMN_ADDED")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    check()
