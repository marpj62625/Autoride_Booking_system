import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from app import app, get_cursor

with app.app_context():
    cur = get_cursor()
    cur.execute("SELECT key, value FROM settings WHERE key ILIKE '%oauth%' OR key ILIKE '%google%' OR key ILIKE '%email%' OR key ILIKE '%smtp%' OR key ILIKE '%client%'")
    rows = cur.fetchall()
    print("MATCHING SETTINGS KEYS:")
    for r in rows:
        v = str(r['value']) if r['value'] is not None else 'None'
        print(f"  {r['key']}: {v[:15]}... (len {len(v)})")
    cur.close()
