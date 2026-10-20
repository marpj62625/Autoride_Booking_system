import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
from app import app, get_cursor

with app.app_context():
    cur = get_cursor()
    cur.execute("""
        SELECT tc.constraint_name, tc.constraint_type, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_name = 'bookings'
    """)
    print("Constraints on bookings:")
    for r in cur.fetchall():
        print(f"  {r['constraint_type']}: {r['column_name']} ({r['constraint_name']})")
