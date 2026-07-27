import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from database import get_connection, release_connection

conn = get_connection()
cur = conn.cursor()
cur.execute("""
    SELECT column_name, column_default, is_generated 
    FROM information_schema.columns 
    WHERE table_name='users' 
    AND column_name IN ('full_name','first_name','middle_name','last_name')
    ORDER BY column_name
""")
rows = cur.fetchall()
for r in rows:
    print(r)
cur.close()
release_connection(conn)
