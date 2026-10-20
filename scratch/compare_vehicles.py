import sys, psycopg, re
sys.path.insert(0, 'AutorideSystem/backend')
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row

with open('AutorideSystem/scratch/pasted_calendar.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()

csv_vehs = set()
for l in lines:
    parts = l.split(',')
    c0 = parts[0].strip()
    if c0 and not any(k in c0.upper() for k in ['CAR MAKE', 'SALES', 'RATE', 'TOTAL']):
        csv_vehs.add(c0)

conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)
cur.execute('SELECT id, name, plate_number, brand, model FROM vehicles')
db_vehs = cur.fetchall()
conn.close()

db_plates = {re.sub(r'[^A-Z0-9]', '', (v['plate_number'] or '').upper()): v for v in db_vehs}
print('=== VEHICLES IN DATABASE ===')
for v in db_vehs:
    print(f"- ID {v['id']}: {v['brand']} {v['model']} ({v['plate_number']})")

print('\n=== VEHICLES IN PASTED CSV ===')
new_vehs = []
matched_vehs = []
for cv in sorted(csv_vehs):
    m = re.search(r'[A-Z]{2,3}\s*\d{3,4}', cv.upper())
    p_clean = re.sub(r'[^A-Z0-9]', '', m.group(0)) if m else ''
    if p_clean in db_plates:
        matched_vehs.append((cv, p_clean, db_plates[p_clean]))
    else:
        new_vehs.append((cv, p_clean))

print(f"\nMATCHED VEHICLES ({len(matched_vehs)}):")
for cv, p, dbv in matched_vehs:
    print(f"  [OK] '{cv}' -> Matched DB ID #{dbv['id']} ({dbv['plate_number']})")

print(f"\nNEW / UNREGISTERED VEHICLES IN CSV ({len(new_vehs)}):")
for cv, p in new_vehs:
    print(f"  [NEW] '{cv}' (Extracted Plate: '{p}')")
