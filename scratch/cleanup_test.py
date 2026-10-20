import sys, psycopg
sys.path.insert(0, 'AutorideSystem/backend')
from config import SUPABASE_DB_URL

conn = psycopg.connect(conninfo=SUPABASE_DB_URL, autocommit=True)
with conn.cursor() as cur:
    cur.execute("DELETE FROM bookings WHERE customer_name = 'Test New Customer QA'")
    cur.execute("DELETE FROM users WHERE first_name = 'Test' AND last_name = 'New Customer QA'")
    print('Cleaned up test records.')
conn.close()
