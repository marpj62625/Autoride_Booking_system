import psycopg
from config import SUPABASE_DB_URL

def migrate_names():
    conn = None
    try:
        conn = psycopg.connect(SUPABASE_DB_URL)
        cursor = conn.cursor()

        # Check if first_name already exists to avoid duplicate work
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' and column_name='first_name'
        """)
        if cursor.fetchone():
            print("first_name column already exists. Checking if full_name is a generated column...")
            # Check if full_name is generated
            cursor.execute("""
                SELECT is_generated 
                FROM information_schema.columns 
                WHERE table_name='users' and column_name='full_name'
            """)
            res = cursor.fetchone()
            if res and res[0] == 'ALWAYS':
                print("Migration already fully applied. Exiting.")
                return
            else:
                print("first_name exists but full_name is not generated. Fixing...")

        # 1. Add new columns
        print("Adding name columns...")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(50)")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS middle_name VARCHAR(50)")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(50)")

        # 2. Extract first and last names from existing full_name
        print("Splitting existing full_name...")
        cursor.execute("""
            UPDATE users SET 
                first_name = split_part(full_name, ' ', 1),
                last_name = CASE 
                                WHEN strpos(full_name, ' ') > 0 THEN substr(full_name, strpos(full_name, ' ') + 1)
                                ELSE ''
                            END
            WHERE full_name IS NOT NULL AND first_name IS NULL
        """)

        # 3. Drop existing full_name column and add it back as a generated column
        print("Converting full_name to generated column...")
        cursor.execute("ALTER TABLE users DROP COLUMN IF EXISTS full_name")
        cursor.execute("""
            ALTER TABLE users ADD COLUMN full_name VARCHAR(255) GENERATED ALWAYS AS (
                TRIM(
                    COALESCE(first_name, '') || 
                    CASE WHEN middle_name IS NOT NULL AND middle_name <> '' THEN ' ' || middle_name ELSE '' END ||
                    CASE WHEN last_name IS NOT NULL AND last_name <> '' THEN ' ' || last_name ELSE '' END
                )
            ) STORED
        """)

        conn.commit()
        print("Migration completed successfully.")
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    migrate_names()
