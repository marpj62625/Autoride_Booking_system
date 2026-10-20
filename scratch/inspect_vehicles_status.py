import sys
sys.path.insert(0, 'backend')
import psycopg2
from config import SUPABASE_DB_URL
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(SUPABASE_DB_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

cur.execute('SELECT id, brand, model, plate_number, status FROM vehicles ORDER BY id ASC;')
rows = cur.fetchall()
print(f'Total vehicles: {len(rows)}')
for r in rows:
    print(f"ID: {r['id']} | {r['brand']} {r['model']} [{r['plate_number']}] | Status: '{r['status']}'")

cur.execute('SELECT status, COUNT(*) as cnt FROM vehicles GROUP BY status ORDER BY cnt DESC;')
print('\nDistinct statuses in vehicles:')
for s in cur.fetchall():
    print(f"  Status: '{s['status']}' -> count: {s['cnt']}")

conn.close()
