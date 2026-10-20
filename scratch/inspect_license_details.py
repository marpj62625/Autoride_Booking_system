import sys
sys.path.append('backend')
import psycopg
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row

conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)

for t in ['license_details', 'notifications']:
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{t}'
        ORDER BY ordinal_position
    """)
    cols = [(c['column_name'], c['data_type']) for c in cur.fetchall()]
    print(f"\nColumns for {t}:")
    for col, dt in cols:
        print(f"  {col}: {dt}")

print("\n--- SAMPLE license_details ---")
cur.execute("SELECT * FROM license_details LIMIT 5")
for r in cur.fetchall():
    print(dict(r))

cur.close()
conn.close()
