import sys
sys.path.insert(0, 'backend')
import psycopg2
from config import SUPABASE_DB_URL

conn = psycopg2.connect(SUPABASE_DB_URL)
cur = conn.cursor()

print("1. Adding address column to license_details if not exists...")
cur.execute("ALTER TABLE license_details ADD COLUMN IF NOT EXISTS address TEXT;")

print("2. Backfilling address from issuing_country_state...")
cur.execute("""
    UPDATE license_details
    SET address = issuing_country_state
    WHERE (address IS NULL OR address = '')
      AND issuing_country_state IS NOT NULL
      AND issuing_country_state != '';
""")
print(f"Updated {cur.rowcount} rows.")

conn.commit()

print("3. Verifying updated rows in license_details:")
cur.execute("SELECT user_id, full_name, license_number, address, issuing_country_state FROM license_details ORDER BY user_id ASC")
rows = cur.fetchall()
for r in rows:
    print(r)

conn.close()
print("Migration completed successfully!")
