import os
import sys
import psycopg

# Append the parent directories to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import SUPABASE_DB_URL

def migrate():
    print("Connecting to Supabase PostgreSQL...")
    conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
    cur = conn.cursor()
    
    try:
        print("Creating addons table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS addons (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                price_per_day NUMERIC(10,2) NOT NULL,
                description TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        print("Inserting default addons if not present...")
        # Check if default addons exist
        cur.execute("SELECT COUNT(*) FROM addons")
        count = cur.fetchone()[0]
        if count == 0:
            cur.execute("""
                INSERT INTO addons (name, price_per_day, description) VALUES
                ('Child Safety Seat', 150.00, 'Standard child seat for security.'),
                ('Roadside Assistance', 100.00, '24/7 towing and roadside service.')
            """)
            print("Default addons inserted.")
        else:
            print("Addons table already has entries, skipping default inserts.")
            
        conn.commit()
        print("Migration completed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise e
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    migrate()
