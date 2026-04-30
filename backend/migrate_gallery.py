import psycopg
from config import SUPABASE_DB_URL

def migrate():
    try:
        with psycopg.connect(SUPABASE_DB_URL) as conn:
            with conn.cursor() as cur:
                print("Checking for vehicle_images table...")
                cur.execute("SELECT to_regclass('public.vehicle_images');")
                if not cur.fetchone()[0]:
                    print("Table vehicle_images does not exist. Creating it...")
                    cur.execute("""
                        CREATE TABLE vehicle_images (
                            id SERIAL PRIMARY KEY,
                            vehicle_id INTEGER REFERENCES vehicles(id) ON DELETE CASCADE,
                            image_path TEXT NOT NULL,
                            is_primary BOOLEAN DEFAULT FALSE,
                            order_index INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                else:
                    print("Table vehicle_images exists. Checking for order_index column...")
                    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='vehicle_images' AND column_name='order_index';")
                    if not cur.fetchone():
                        print("Adding order_index column...")
                        cur.execute("ALTER TABLE vehicle_images ADD COLUMN order_index INTEGER DEFAULT 0;")
                    else:
                        print("order_index column already exists.")
                
                conn.commit()
                print("Migration successful.")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
