import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
from app import app, get_cursor

with app.app_context():
    cur = get_cursor()
    cur.execute("""
        SELECT column_name, is_nullable, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'bookings'
        ORDER BY ordinal_position
    """)
    rows = cur.fetchall()
    print("Bookings table columns:")
    for r in rows:
        print(f"  {r['column_name']} ({r['data_type']}, nullable: {r['is_nullable']})")
