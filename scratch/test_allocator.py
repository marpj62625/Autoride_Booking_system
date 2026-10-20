import sys, os, datetime
sys.path.append(os.path.abspath('backend'))
from database import get_connection
from psycopg.rows import dict_row

conn = get_connection()
cur = conn.cursor(row_factory=dict_row)

user_ids = [25, 26, 27, 28, 29, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]
cur.execute("SELECT id, full_name, phone, email FROM users WHERE id = ANY(%s) ORDER BY id ASC", (user_ids,))
users = {u['id']: u for u in cur.fetchall()}

# Get all current DB bookings for the 16 users from Sept 2026 onwards
cur.execute("""
    SELECT b.id, b.user_id, b.vehicle_id, b.start_date, b.end_date
    FROM bookings b
    WHERE b.user_id = ANY(%s) AND b.end_date >= '2026-09-01'
""", (user_ids,))
existing_db_bookings = cur.fetchall()

# Map vehicles
cur.execute("SELECT id, brand, model, plate_number FROM vehicles")
vehicles = {v['id']: v for v in cur.fetchall()}

def get_veh_by_plate(plate_sub):
    for vid, v in vehicles.items():
        if plate_sub.replace(' ', '').lower() in v['plate_number'].replace(' ', '').lower():
            return v
    return None

# The 13 new booking slots
slots = [
    {
        'label': 'Toyota Vios XE AT Gray [DAT 1396]',
        'veh_id': get_veh_by_plate('DAT 1396')['id'],
        'start_date': datetime.date(2026, 10, 1),
        'end_date': datetime.date(2026, 10, 1),
        'orig_cust': 'JOSH YOUAYN MALLARI',
        'rate': 1800.0,
    },
    {
        'label': 'Toyota Innova XE AT [CCK 1126]',
        'veh_id': get_veh_by_plate('CCK 1126')['id'],
        'start_date': datetime.date(2026, 10, 1),
        'end_date': datetime.date(2026, 10, 30),
        'orig_cust': 'MERRY JOY TORRES',
        'rate': 2500.0 * 30,
    },
    {
        'label': 'Honda BR-V [NID 2724]',
        'veh_id': get_veh_by_plate('NID 2724')['id'],
        'start_date': datetime.date(2026, 10, 6),
        'end_date': datetime.date(2026, 10, 13),
        'orig_cust': 'JOEM MARK REYES BULOTANO',
        'rate': 2600.0 * 8,
    },
    {
        'label': 'Toyota Innova XE AT [NHN 5388]',
        'veh_id': get_veh_by_plate('NHN 5388')['id'],
        'start_date': datetime.date(2026, 10, 6),
        'end_date': datetime.date(2026, 10, 8),
        'orig_cust': 'JAY KARL GONZALES',
        'rate': 2500.0 * 3,
    },
    {
        'label': 'Toyota Vios XE AT Gray [DAT 1396]',
        'veh_id': get_veh_by_plate('DAT 1396')['id'],
        'start_date': datetime.date(2026, 10, 10),
        'end_date': datetime.date(2026, 10, 11),
        'orig_cust': 'JAYMIE CACHERO',
        'rate': 1800.0 * 2,
    },
    {
        'label': 'Toyota Vios XE AT Gray [DAT 1396]',
        'veh_id': get_veh_by_plate('DAT 1396')['id'],
        'start_date': datetime.date(2026, 10, 12),
        'end_date': datetime.date(2026, 10, 17),
        'orig_cust': 'SHARMAINE BERNABE RUTAQUIO',
        'rate': 1800.0 * 6,
    },
    {
        'label': 'Toyota Innova XE AT [NHN 5388]',
        'veh_id': get_veh_by_plate('NHN 5388')['id'],
        'start_date': datetime.date(2026, 10, 12),
        'end_date': datetime.date(2026, 10, 19),
        'orig_cust': 'SUNLINE ELECTRONICS',
        'rate': 2500.0 * 8,
    },
    {
        'label': 'Toyota Vios J MT [NCX 4117]',
        'veh_id': get_veh_by_plate('NCX 4117')['id'],
        'start_date': datetime.date(2026, 10, 14),
        'end_date': datetime.date(2026, 10, 14),
        'orig_cust': 'JESTONI CHRISTIAN PASCO',
        'rate': 1500.0,
    },
    {
        'label': 'Toyota Vios XLE AT Blue [DBJ 9483]',
        'veh_id': get_veh_by_plate('DBJ 9483')['id'],
        'start_date': datetime.date(2026, 10, 15),
        'end_date': datetime.date(2026, 10, 16),
        'orig_cust': 'GOMER MERCADO',
        'rate': 1800.0 * 2,
    },
    {
        'label': 'Toyota Vios J MT [NCX 4117]',
        'veh_id': get_veh_by_plate('NCX 4117')['id'],
        'start_date': datetime.date(2026, 10, 30),
        'end_date': datetime.date(2026, 10, 30),
        'orig_cust': 'KHYM CRUZ - SANCHEZ',
        'rate': 1500.0,
    },
    {
        'label': 'Toyota Vios J MT [NCX 4117]',
        'veh_id': get_veh_by_plate('NCX 4117')['id'],
        'start_date': datetime.date(2026, 11, 1),
        'end_date': datetime.date(2026, 11, 2),
        'orig_cust': 'HUBBERT SANCHEZ',
        'rate': 1500.0 * 2,
    },
    {
        'label': 'Toyota Vios J MT [NCX 4117]',
        'veh_id': get_veh_by_plate('NCX 4117')['id'],
        'start_date': datetime.date(2026, 12, 9),
        'end_date': datetime.date(2026, 12, 10),
        'orig_cust': 'MICHAELLA ANGELA TABLASON',
        'rate': 1500.0 * 2,
    },
    {
        'label': 'Toyota Innova XE AT [NHN 5388]',
        'veh_id': get_veh_by_plate('NHN 5388')['id'],
        'start_date': datetime.date(2026, 12, 23),
        'end_date': datetime.date(2026, 12, 29),
        'orig_cust': 'JAY-AR CABILES',
        'rate': 2500.0 * 7,
    }
]

# Track simulated bookings per user
user_schedule = {uid: [] for uid in user_ids}
for eb in existing_db_bookings:
    user_schedule[eb['user_id']].append({
        'start_date': eb['start_date'],
        'end_date': eb['end_date'],
        'vehicle_id': eb['vehicle_id']
    })

def has_conflict(uid, s_date, e_date, v_id):
    for b in user_schedule[uid]:
        # Rule 1: No overlap
        if s_date <= b['end_date'] and e_date >= b['start_date']:
            return True, "Date overlap"
        # Rule 2: No next-day or previous-day booking on a different vehicle
        # End date of one booking and start date of another within 1 day on different vehicles
        gap_before = (s_date - b['end_date']).days
        gap_after = (b['start_date'] - e_date).days
        if gap_before in (0, 1) and b['vehicle_id'] != v_id:
            return True, f"Too close to previous booking ending {b['end_date']} on veh {b['vehicle_id']}"
        if gap_after in (0, 1) and b['vehicle_id'] != v_id:
            return True, f"Too close to next booking starting {b['start_date']} on veh {b['vehicle_id']}"
    return False, "OK"

allocations = []
# Prioritize users who have the fewest total bookings in Oct-Dec
for slot in slots:
    s_date = slot['start_date']
    e_date = slot['end_date']
    v_id = slot['veh_id']
    
    # Sort candidate users by number of Oct-Dec bookings, then total bookings
    candidates = []
    for uid in user_ids:
        conflict, reason = has_conflict(uid, s_date, e_date, v_id)
        if not conflict:
            # count Oct-Dec bookings
            oct_dec_count = sum(1 for b in user_schedule[uid] if b['end_date'] >= datetime.date(2026, 10, 1))
            total_count = len(user_schedule[uid])
            candidates.append((oct_dec_count, total_count, uid))
            
    candidates.sort() # lowest count first
    if not candidates:
        print(f"ERROR: No conflict-free user found for slot: {slot['orig_cust']} ({s_date} -> {e_date})")
    else:
        chosen_uid = candidates[0][2]
        user_schedule[chosen_uid].append({
            'start_date': s_date,
            'end_date': e_date,
            'vehicle_id': v_id
        })
        allocations.append({
            'slot': slot,
            'user': users[chosen_uid]
        })

print("\n=== PROPOSED CONFLICT-FREE ALLOCATION PLAN ===")
for a in allocations:
    s = a['slot']
    u = a['user']
    print(f"Slot: {s['start_date']} to {s['end_date']} | {s['label']}")
    print(f"  -> Original CSV Name: '{s['orig_cust']}'")
    print(f"  -> ALLOCATED TO: User #{u['id']} - {u['full_name']} ({u['email']})")
    print()

# Summary per user
print("=== OCT-DEC 2026 BOOKING COUNT PER USER AFTER ALLOCATION ===")
for uid in user_ids:
    u = users[uid]
    bks = [b for b in user_schedule[uid] if b['end_date'] >= datetime.date(2026, 10, 1)]
    bk_desc = ', '.join([f"{b['start_date']}->{b['end_date']} (veh {b['vehicle_id']})" for b in bks])
    print(f"User #{uid} ({u['full_name']}): {len(bks)} bookings | [{bk_desc}]")

conn.close()
