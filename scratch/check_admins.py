import sys
sys.path.append('backend')
import psycopg
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row

conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)

cur.execute("SELECT * FROM admins")
print("Admins table:")
for r in cur.fetchall():
    print(dict(r))

cur.execute("SELECT id, user_id, role, full_name, email FROM users WHERE role LIKE '%admin%'")
print("\nUsers table admins:")
for r in cur.fetchall():
    print(dict(r))

cur.close()
conn.close()
