import sys
import os

# Add backend to path to import database
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import psycopg
from config import SUPABASE_DB_URL

def execute_sql_file(filename):
    try:
        # Connect using the URL from config.py
        with psycopg.connect(SUPABASE_DB_URL) as conn:
            with conn.cursor() as cur:
                with open(filename, 'r') as f:
                    sql = f.read()
                cur.execute(sql)
                print(f"Successfully executed {filename}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    execute_sql_file(r"c:\Users\patri\OneDrive\Desktop\AutorideSystem2side\AutorideSystem\backend\create_coupons.sql")
