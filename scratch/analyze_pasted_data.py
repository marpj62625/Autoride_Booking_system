import sys, csv, datetime, re
sys.path.insert(0, 'AutorideSystem/backend')
from config import SUPABASE_DB_URL
import psycopg
from psycopg.rows import dict_row

def parse_csv_calendar(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))

    records = []
    current_year = None
    current_month = None
    day_indices = {} # col_idx -> int day

    non_customers = {
        'CAR MAKE', 'PICK-UP', 'PICKUP', 'DROP-OFF', 'DROPOFF', 'OFF',
        'MAINTENANCE', 'REPAIR', 'AVAILABLE', 'RESERVED', 'INSPECTION',
        'CLEANING', 'PULL OUT', 'PULL-OUT', 'TOTAL', 'RATE', 'SALES',
        'NONE', 'N/A', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN', 'MON',
        'JUNE - SALES', 'TOTAL SALES JUNE 2025'
    }

    for r_idx, row in enumerate(reader):
        if not row or not any(row):
            continue
        first_cell = row[0].strip()

        # Month Header check
        if 'CAR MAKE' in first_cell.upper():
            day_indices = {}
            current_year = None
            current_month = None
            # Find date in header
            for val in row[1:]:
                val = val.strip()
                if not val: continue
                # Match YYYY-MM-DD
                m_date = re.search(r'(\d{4})-(\d{2})-\d{2}', val)
                if m_date:
                    current_year = int(m_date.group(1))
                    current_month = int(m_date.group(2))
                    break
                # Match "ARPIL 2025" or "APRIL 2025"
                val_u = val.upper().replace('ARP', 'APR')
                m_txt = re.search(r'([A-Z]+)\s*(\d{4})', val_u)
                if m_txt:
                    m_name, y_str = m_txt.groups()
                    months = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']
                    for idx, mn in enumerate(months, 1):
                        if mn.startswith(m_name[:3]):
                            current_year = int(y_str)
                            current_month = idx
                            break
                    if current_year: break
            continue

        # Day Number Header check (1, 2, 3...)
        # Check if row has integers 1, 2, 3...
        digits = []
        for c_idx, cell in enumerate(row):
            cell_clean = cell.strip()
            if cell_clean.isdigit():
                val = int(cell_clean)
                if 1 <= val <= 31:
                    digits.append((c_idx, val))
        if len(digits) >= 15:
            day_indices = {c_idx: val for c_idx, val in digits}
            continue

        # Vehicle Row check
        if first_cell and day_indices and current_year and current_month:
            # Check if this is a vehicle or a summary row
            if any(k in first_cell.upper() for k in ['SALES', 'RATE', 'TOTAL', 'EXPENSES', 'SUMMARY']):
                continue

            veh_name = first_cell
            # Scan columns for customer bookings
            curr_cust = None
            start_day = None
            last_day = None

            sorted_cols = sorted(day_indices.keys())
            for c_idx in sorted_cols:
                day_val = day_indices[c_idx]
                cell_val = row[c_idx].strip() if c_idx < len(row) else ''

                is_cust = (
                    bool(cell_val) and
                    cell_val.upper() not in non_customers and
                    not cell_val.isdigit() and
                    len(cell_val) > 2 and
                    not any(k in cell_val.upper() for k in ['SALES', 'RATE', 'TOTAL'])
                )

                if is_cust:
                    if curr_cust and cell_val.upper() == curr_cust.upper():
                        last_day = day_val
                    else:
                        if curr_cust and start_day and last_day:
                            records.append({
                                'vehicle': veh_name,
                                'customer': curr_cust,
                                'start_date': f"{current_year}-{current_month:02d}-{start_day:02d}",
                                'end_date': f"{current_year}-{current_month:02d}-{last_day:02d}",
                                'year_month': f"{current_year}-{current_month:02d}"
                            })
                        curr_cust = cell_val
                        start_day = day_val
                        last_day = day_val
                else:
                    # Gap / Empty cell
                    # If empty, but previous booking continues?
                    # In CSV without merged cells, empty cells mean booking ended or was 1 day
                    if curr_cust and start_day and last_day:
                        records.append({
                            'vehicle': veh_name,
                            'customer': curr_cust,
                            'start_date': f"{current_year}-{current_month:02d}-{start_day:02d}",
                            'end_date': f"{current_year}-{current_month:02d}-{last_day:02d}",
                            'year_month': f"{current_year}-{current_month:02d}"
                        })
                        curr_cust = None
                        start_day = None
                        last_day = None

            if curr_cust and start_day and last_day:
                records.append({
                    'vehicle': veh_name,
                    'customer': curr_cust,
                    'start_date': f"{current_year}-{current_month:02d}-{start_day:02d}",
                    'end_date': f"{current_year}-{current_month:02d}-{last_day:02d}",
                    'year_month': f"{current_year}-{current_month:02d}"
                })

    return records

parsed = parse_csv_calendar('AutorideSystem/scratch/pasted_calendar.csv')
print(f'Total bookings parsed from pasted CSV: {len(parsed)}')

# Group by month
by_month = {}
for p in parsed:
    by_month.setdefault(p['year_month'], []).append(p)

for ym in sorted(by_month.keys()):
    print(f"Month {ym}: {len(by_month[ym])} bookings")

# Now connect to database and compare!
conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)

cur.execute("""
    SELECT b.id, b.start_date, b.end_date, b.customer_name, b.status,
           u.full_name as user_name, v.plate_number, v.name as vehicle_name,
           v.brand, v.model
    FROM bookings b
    LEFT JOIN users u ON b.user_id = u.id
    LEFT JOIN vehicles v ON b.vehicle_id = v.id
""")
db_bookings = cur.fetchall()
conn.close()

print(f"Total existing bookings in database: {len(db_bookings)}")

# Helper to normalize strings
def norm(s):
    return re.sub(r'[^a-zA-Z0-9]', '', str(s or '').lower())

# Match parsed bookings against db
already_in_db = []
new_in_csv = []

for p in parsed:
    p_cust = norm(p['customer'])
    p_start = p['start_date']
    p_end = p['end_date']
    
    # Extract plate from vehicle string if possible
    # e.g., 'NCX 4117' or 'DAT 1396' or 'NID 2724'
    plate_match = re.search(r'[A-Z]{2,3}\s*\d{3,4}', p['vehicle'].upper())
    p_plate = norm(plate_match.group(0)) if plate_match else norm(p['vehicle'])

    match_found = False
    for db in db_bookings:
        db_start = str(db['start_date'])[:10]
        db_end = str(db['end_date'])[:10]
        db_cust = norm(db['customer_name'] or db['user_name'])
        db_plate = norm(db['plate_number'])

        # Check if matches customer or plate + overlapping/exact date
        # 1. Exact match on date and customer
        if p_start == db_start and (p_cust in db_cust or db_cust in p_cust) and len(p_cust) > 3:
            match_found = True
            break
        # 2. Same customer and same month and dates close
        if (p_cust in db_cust or db_cust in p_cust) and len(p_cust) > 4 and p['year_month'] in db_start:
            match_found = True
            break

    if match_found:
        already_in_db.append(p)
    else:
        new_in_csv.append(p)

print(f"\nRESULTS:")
print(f"Already in database: {len(already_in_db)}")
print(f"NEW (Wala pa sa database): {len(new_in_csv)}")

print("\n--- SAMPLE OF NEW ENTRIES ---")
for n in new_in_csv[:25]:
    print(f"- [{n['year_month']}] {n['vehicle']} | {n['customer']} ({n['start_date']} to {n['end_date']})")
