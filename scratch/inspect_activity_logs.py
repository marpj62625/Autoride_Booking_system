import sys
sys.path.append('backend')
import psycopg
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row

conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)

cur.execute("""
    SELECT column_name, data_type, column_default, is_nullable
    FROM information_schema.columns 
    WHERE table_name = 'activity_logs'
    ORDER BY ordinal_position
""")
print("--- ACTIVITY_LOGS COLUMNS ---")
for c in cur.fetchall():
    print(dict(c))

print("\n--- SAMPLE APPROVE ACTIVITY LOGS ---")
cur.execute("""
    SELECT * FROM activity_logs 
    WHERE action ILIKE '%approve%' OR action ILIKE '%verif%'
    ORDER BY created_at DESC 
    LIMIT 10
""")
for r in cur.fetchall():
    print(dict(r))

print("\n--- DISTINCT ACTIONS IN ACTIVITY LOGS ---")
cur.execute("SELECT action, COUNT(*) as cnt FROM activity_logs GROUP BY action ORDER BY cnt DESC LIMIT 20")
for r in cur.fetchall():
    print(dict(r))

cur.close()
conn.close()
