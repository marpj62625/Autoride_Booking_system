import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
from app import app, get_cursor

with app.app_context():
    cur = get_cursor()
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%otp%'
    """)
    rows = cur.fetchall()
    print("Tables with 'otp':", [r['table_name'] for r in rows])
