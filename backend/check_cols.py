import psycopg
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row

conn = psycopg.connect(SUPABASE_DB_URL, row_factory=dict_row)
cur = conn.cursor()

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'notifications'
""")
cols = cur.fetchall()
for c in cols:
    print(c)
