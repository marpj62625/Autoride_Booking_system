import sys
sys.path.insert(0, 'backend')
import psycopg2
from config import SUPABASE_DB_URL

conn = psycopg2.connect(SUPABASE_DB_URL)
cur = conn.cursor()

print("--- Sample license_details rows ---")
cur.execute("""
    SELECT ld.user_id, ld.full_name, ld.license_number, ld.issuing_country_state
    FROM license_details ld
    ORDER BY ld.user_id ASC
""")
rows = cur.fetchall()
print(f"Total rows in license_details: {len(rows)}")
for r in rows:
    print(r)
conn.close()
