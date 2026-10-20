import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
from app import app, get_cursor

with app.app_context():
    cur = get_cursor()
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'payments'
        ORDER BY ordinal_position
    """)
    print("Payments columns:")
    for r in cur.fetchall():
        print(f"  {r['column_name']} ({r['data_type']})")
