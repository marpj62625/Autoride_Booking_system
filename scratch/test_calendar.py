import sys, os
sys.path.append('AutorideSystem/backend')
from config import SUPABASE_DB_URL
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(SUPABASE_DB_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)
cur.execute("SELECT id, start_date, end_date, start_time, end_time, vehicle_id, customer_name FROM bookings WHERE status NOT IN ('cancelled', 'rejected') ORDER BY id DESC LIMIT 10")
bookings = cur.fetchall()
for b in bookings:
    print(dict(b))
