import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from database import get_connection, release_connection

def add_generated_column():
    conn = get_connection()
    cur = conn.cursor()
    try:
        print("Adding generated full_name column...")
        cur.execute("""
            ALTER TABLE users 
            ADD COLUMN full_name VARCHAR(255) 
            GENERATED ALWAYS AS (
                TRIM(regexp_replace(
                    COALESCE(first_name, '') || ' ' || 
                    COALESCE(NULLIF(middle_name, ''), '') || ' ' || 
                    COALESCE(last_name, ''), 
                    '\s+', ' ', 'g'
                ))
            ) STORED;
        """)
        conn.commit()
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cur.close()
        release_connection(conn)

if __name__ == "__main__":
    add_generated_column()
