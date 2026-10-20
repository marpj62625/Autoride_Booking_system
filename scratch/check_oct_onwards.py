import sys, csv, psycopg, re
sys.path.insert(0, 'AutorideSystem/backend')
sys.path.insert(0, 'AutorideSystem')
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row
from scratch.analyze_pasted_data import parse_csv_calendar

# 1. Parse CSV bookings from Oct 2026 onwards
csv_bookings = parse_csv_calendar('AutorideSystem/scratch/pasted_calendar.csv')
oct_plus = [c for c in csv_bookings if c['year_month'] >= '2026-10']

print(f"Total CSV bookings from Oct 2026 onwards: {len(oct_plus)}")

# 2. Connect to database and fetch 16 users and all bookings Oct onwards
conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)

user_ids = [25, 26, 27, 28, 29, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]
cur.execute("SELECT id, full_name, email, phone FROM users WHERE id = ANY(%s)", (user_ids,))
users_16 = {u['id']: u for u in cur.fetchall()}

cur.execute("""
    SELECT b.id, b.user_id, u.full_name as user_name, b.customer_name,
           b.vehicle_id, v.brand, v.model, v.plate_number,
           b.start_date, b.end_date, b.status
    FROM bookings b
    LEFT JOIN users u ON b.user_id = u.id
    LEFT JOIN vehicles v ON b.vehicle_id = v.id
    WHERE b.start_date >= '2026-10-01'
    ORDER BY b.start_date ASC
""")
db_oct_bookings = cur.fetchall()
conn.close()

def norm(s):
    return re.sub(r'[^a-zA-Z0-9]', '', str(s or '').lower())

# Check each CSV booking
print("\n=== ALL CSV ENTRIES FROM OCT 2026 ONWARDS ===")
for cb in oct_plus:
    cb_cust = cb['customer']
    cb_veh = cb['vehicle']
    cb_start = cb['start_date']
    cb_end = cb['end_date']
    cb_norm_cust = norm(cb_cust)

    # 1. Check if matches any of the 16 users by name
    matched_16_user = None
    for uid, u in users_16.items():
        u_norm = norm(u['full_name'])
        # check partial words
        u_parts = [p.lower() for p in re.findall(r'[a-zA-Z]{3,}', u['full_name'])]
        cb_parts = [p.lower() for p in re.findall(r'[a-zA-Z]{3,}', cb_cust)]
        overlap = set(u_parts).intersection(set(cb_parts))
        # Ignore common filler words
        overlap = {w for w in overlap if w not in ['delos', 'reyes', 'san']}
        if len(overlap) >= 2 or (len(overlap) == 1 and any(len(w) >= 6 for w in overlap)):
            matched_16_user = u
            break
        if cb_norm_cust in u_norm or u_norm in cb_norm_cust:
            matched_16_user = u
            break

    # 2. Check if already in DB
    in_db = False
    db_match_info = None
    for db in db_oct_bookings:
        db_start = str(db['start_date'])[:10]
        db_cust = norm(db['customer_name'] or db['user_name'])
        if cb_start == db_start and (cb_norm_cust in db_cust or db_cust in cb_norm_cust) and len(cb_norm_cust) > 3:
            in_db = True
            db_match_info = db
            break

    user_match_str = f"*** MATCHES 16 USER: User #{matched_16_user['id']} ({matched_16_user['full_name']}) ***" if matched_16_user else "No 16-user match"
    status_str = f"ALREADY IN DB (ID #{db_match_info['id']})" if in_db else "NEW (WALA PA SA DB)"

    print(f"[{cb['year_month']}] {cb_start} to {cb_end} | {cb_veh} | Customer: '{cb_cust}'")
    print(f"    -> Status: {status_str}")
    print(f"    -> 16 Users Check: {user_match_str}")
    print()
