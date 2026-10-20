import sys
sys.path.append('backend')
import psycopg
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row

conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)

cur.execute("""
    SELECT id, user_id, full_name, email, created_at, role
    FROM users
    WHERE role = 'customer' OR role IS NULL
    ORDER BY id
""")
rows = cur.fetchall()
print(f"Total customers: {len(rows)}")
for u in rows:
    print(f"ID={u['id']} | {u['full_name']} | {u['email']} | Reg: {u['created_at']}")

cur.close()
conn.close()
