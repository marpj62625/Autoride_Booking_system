import sys
import os

# Add backend to path so we can import database
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database import get_connection, release_connection
from psycopg.rows import dict_row

def migrate_names():
    conn = get_connection()
    cur = conn.cursor(row_factory=dict_row)
    if not cur:
        print("Failed to get database cursor.")
        return

    try:
        # Add new columns
        print("Adding new name columns...")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(50);")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS middle_name VARCHAR(50);")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(50);")
        
        # Check if full_name column exists before migrating
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='full_name';")
        if not cur.fetchone():
            print("Column 'full_name' already dropped or does not exist.")
            return

        # Fetch all users
        print("Fetching existing users...")
        cur.execute("SELECT id, full_name FROM users WHERE full_name IS NOT NULL;")
        users = cur.fetchall()

        print(f"Found {len(users)} users to migrate.")

        for user in users:
            uid = user['id']
            full_name = user['full_name'].strip()
            
            parts = full_name.split()
            first_name = ""
            middle_name = ""
            last_name = ""

            if len(parts) == 1:
                first_name = parts[0]
            elif len(parts) == 2:
                first_name = parts[0]
                last_name = parts[1]
            elif len(parts) >= 3:
                first_name = parts[0]
                last_name = parts[-1]
                middle_name = " ".join(parts[1:-1])

            # Update the user
            cur.execute(
                "UPDATE users SET first_name = %s, middle_name = %s, last_name = %s WHERE id = %s",
                (first_name, middle_name, last_name, uid)
            )

        print("Data split completed.")
        
        # Drop the full_name column
        print("Dropping 'full_name' column...")
        cur.execute("ALTER TABLE users DROP COLUMN full_name;")
        
        conn.commit()
        print("Migration successful.")

    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        cur.close()
        release_connection(conn)

if __name__ == "__main__":
    migrate_names()
