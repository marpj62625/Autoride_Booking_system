import sys
sys.path.append('backend')
import psycopg
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row

conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)

cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
""")
tables = [t['table_name'] for t in cur.fetchall()]
print("Tables:", tables)

for t in ['users', 'driver_licenses', 'licenses', 'verifications', 'bookings']:
    if t in tables:
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

cur.close()
conn.close()
