import sys
import os

# Add backend to path to import database config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import psycopg
from config import SUPABASE_DB_URL

def inspect_bookings():
    try:
        print("Connecting to Supabase PostgreSQL...")
        with psycopg.connect(SUPABASE_DB_URL) as conn:
            with conn.cursor() as cur:
                print("Inspecting 'bookings' table...")
                cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'bookings'")
                cols = cur.fetchall()
                for c in cols:
                    print(f"Column: {c[0]}, Type: {c[1]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_bookings()
