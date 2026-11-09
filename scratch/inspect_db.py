import sys
import os
sys.path.insert(0, os.path.abspath('AutorideSystem/backend'))
import psycopg
from config import SUPABASE_DB_URL

conn = psycopg.connect(conninfo=SUPABASE_DB_URL, autocommit=True, prepare_threshold=None)
cur = conn.cursor()

cur.execute("""
    SELECT column_name, column_default, is_nullable
    FROM information_schema.columns 
    WHERE table_name = 'locations'
""")
for r in cur.fetchall():
    print(r)

conn.close()
