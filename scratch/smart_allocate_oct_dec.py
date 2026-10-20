import sys, os, csv, re, datetime
sys.path.append(os.path.abspath('backend'))
from database import get_connection
from psycopg.rows import dict_row

# 1. Parse CSV calendar for Oct-Dec 2026
def parse_oct_dec_calendar(csv_path):
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))

    records = []
    current_year = None
    current_month = None
    day_cols = {} # col_idx -> int day

    for r_idx, row in enumerate(reader):
        if not row or not any(row):
            continue
        first_cell = row[0].strip().upper()
        if 'CAR MAKE' in first_cell:
            current_year = None
            current_month = None
            day_cols = {}
            for c_idx, val in enumerate(row):
                m_date = re.search(r'(\d{4})-(\d{2})-\d{2}', val)
                if m_date:
                    current_year = int(m_date.group(1))
                    current_month = int(m_date.group(2))
                    break
            continue

        # Check day numbers row (row with 1, 2, 3...)
        cleaned = [c.strip() for c in row if c.strip().isdigit()]
        if len(cleaned) >= 15 and current_year and not day_cols:
            for c_idx, val in enumerate(row):
                v = val.strip()
                if v.isdigit():
                    day_cols[c_idx] = int(v)
            continue

        # Vehicle row
        if current_year and current_month and day_cols and row[0].strip():
            car_label = row[0].strip()
            # Scan columns for booking entries
            col_indices = sorted(day_cols.keys())
            c_i = 0
            while c_i < len(col_indices):
                col_idx = col_indices[c_i]
                cell_val = row[col_idx].strip() if col_idx < len(row) else ''
                if cell_val and cell_val.upper() not in ('CAR MAKE', 'NONE', 'N/A', 'AVAILABLE', 'MAINTENANCE', 'REPAIR'):
                    cust_name = cell_val
                    start_day = day_cols[col_idx]
                    end_day = start_day

                    # Extend if next columns have same or empty (merged block)
                    next_i = c_i + 1
                    while next_i < len(col_indices):
                        next_col = col_indices[next_i]
                        next_val = row[next_col].strip() if next_col < len(row) else ''
                        if next_val == cust_name or next_val == '':
                            # check if it's really the same booking span
                            if next_val == cust_name:
                                end_day = day_cols[next_col]
                                next_i += 1
                            else:
                                # empty column, check if next non-empty has something else or if we should stop
                                break
                        else:
                            break
                    c_i = next_i

                    s_date = datetime.date(current_year, current_month, start_day)
                    e_date = datetime.date(current_year, current_month, end_day)

                    records.append({
                        'car_label': car_label,
                        'customer_name': cust_name,
                        'start_date': s_date,
                        'end_date': e_date,
                        'year_month': f"{current_year}-{current_month:02d}"
                    })
                else:
                    c_i += 1
    return records

raw_records = parse_oct_dec_calendar('scratch/oct_dec_calendar.csv')
print(f"Extracted {len(raw_records)} booking records from Oct-Dec 2026 CSV:")
for r in raw_records:
    print(f"  {r['start_date']} -> {r['end_date']} | {r['car_label']} | Cust: {r['customer_name']}")

# 2. Database connection
conn = get_connection()
cur = conn.cursor(row_factory=dict_row)

# Get vehicles
cur.execute("SELECT id, brand, model, plate_number FROM vehicles ORDER BY id ASC")
db_vehicles = cur.fetchall()

def match_vehicle(car_label):
    norm_lbl = re.sub(r'[^a-zA-Z0-9]', '', car_label).lower()
    for v in db_vehicles:
        norm_plt = re.sub(r'[^a-zA-Z0-9]', '', v['plate_number']).lower()
        if norm_plt and norm_plt in norm_lbl:
            return v
    # fallback on model
    for v in db_vehicles:
        norm_mdl = re.sub(r'[^a-zA-Z0-9]', '', v['model']).lower()
        if norm_mdl and norm_mdl in norm_lbl:
            return v
    return None

# Get 16 official users
user_ids = [25, 26, 27, 28, 29, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]
cur.execute("SELECT id, full_name, email, phone FROM users WHERE id = ANY(%s) ORDER BY id ASC", (user_ids,))
users_16 = {u['id']: u for u in cur.fetchall()}

# Get all current bookings for the 16 users from Sept 2026 to Dec 2026
cur.execute("""
    SELECT id, user_id, vehicle_id, customer_name, start_date, end_date, status
    FROM bookings
    WHERE user_id = ANY(%s) AND end_date >= '2026-09-01'
    ORDER BY start_date ASC
""", (user_ids,))
existing_16_bookings = cur.fetchall()

print(f"\nLoaded {len(users_16)} users and {len(existing_16_bookings)} existing bookings for them (Sept 2026 onwards).")

conn.close()
