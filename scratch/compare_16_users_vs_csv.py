import sys, csv, psycopg, re
sys.path.insert(0, 'AutorideSystem/backend')
sys.path.insert(0, 'AutorideSystem')
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row
from scratch.analyze_pasted_data import parse_csv_calendar

conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)

user_ids = [25, 26, 27, 28, 29, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]

cur.execute("""
    SELECT b.id, b.user_id, u.full_name as user_name,
           b.vehicle_id, v.brand, v.model, v.plate_number,
           b.start_date, b.end_date, b.status
    FROM bookings b
    JOIN users u ON b.user_id = u.id
    JOIN vehicles v ON b.vehicle_id = v.id
    WHERE b.user_id = ANY(%s) AND b.start_date >= '2026-09-01'
    ORDER BY b.start_date ASC, b.id ASC
""", (user_ids,))
user_bookings = cur.fetchall()
conn.close()

csv_bookings = parse_csv_calendar('AutorideSystem/scratch/pasted_calendar.csv')
csv_sept_plus = [c for c in csv_bookings if c['year_month'] >= '2026-09']

print(f"16 Users Bookings in DB (Sept 2026 onwards): {len(user_bookings)}")
print(f"CSV Bookings (Sept 2026 onwards): {len(csv_sept_plus)}")

print("\n=== DETAILED ALIGNMENT CHECK ===")
for ub in user_bookings:
    ub_start = str(ub['start_date'])[:10]
    ub_end = str(ub['end_date'])[:10]
    ub_plate = re.sub(r'[^A-Z0-9]', '', (ub['plate_number'] or '').upper())

    overlapping = []
    for cb in csv_sept_plus:
        m = re.search(r'[A-Z]{2,3}\s*\d{3,4}', cb['vehicle'].upper())
        cb_plate = re.sub(r'[^A-Z0-9]', '', m.group(0)) if m else ''
        if cb_plate == ub_plate:
            cb_start = cb['start_date']
            cb_end = cb['end_date']
            if not (ub_end < cb_start or ub_start > cb_end):
                overlapping.append(cb)

    overlap_info = ""
    if overlapping:
        names = ", ".join([f"'{o['customer']}' ({o['start_date']} to {o['end_date']})" for o in overlapping])
        overlap_info = f"-> Ka-date/Tapat sa CSV: {names}"
    else:
        overlap_info = "-> [Walang conflict sa CSV]"

    print(f"DB #{ub['id']} | User #{ub['user_id']} ({ub['user_name']}) | {ub['brand']} {ub['model']} ({ub['plate_number']}) | {ub_start} to {ub_end} {overlap_info}")
