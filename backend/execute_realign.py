import openpyxl
import re
from datetime import datetime, date, timedelta
import sys
import os
from collections import defaultdict
import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.dirname(__file__))
from config import SUPABASE_DB_URL

# 1. Load Excel
EXCEL_PATH = r'C:\Dev\AutorideSystem2sides\AutorideSystem\ARC-MONITORING-2026.xlsx'
wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
sheet = wb['2026']

# 16 Verified Users Mapping (1-to-1 match)
VERIFIED_MAP = {
    'ARVIN CORPUZ': 25,             # Guamil Gabriel Sanchez (User ID 25)
    'HARMAN BHULLAR': 26,           # Michael Jarina (User ID 26)
    'CECILLE VALENCIA': 27,         # Allan Jr. Anas (User ID 27)
    'HUBERT SANCHEZ': 28,           # Villy Arroz (User ID 28)
    'MICHAEL VINCENT': 29,          # Julius Labrador (User ID 29)
    'ALEXANDER ARAMIL': 38,         # Arl Junell Tobias (User ID 38)
    'JOMAR GELI': 39,               # Rolly Pelicano (User ID 39)
    'LAN DAPAT': 40,                # Vicmar Alquino (User ID 40)
    'NORBERT GAMARO': 41,           # Danny Calix (User ID 41)
    'ALLIANA TOLENTINO': 42,        # John Robin Uri (User ID 42)
    'THERESA PANGILINAN': 43,       # Mike Handomon (User ID 43)
    'DANE MARIONNE': 44,            # Eliezer Amador (User ID 44)
    'MARJHERIE CATAPANG': 45,       # Aldwin Maghirang (User ID 45)
    'JOSE MARIE SANTOS': 46,        # Virgilio Ona (User ID 46)
    'CHERRYLYN GARDIOLA': 47,       # Nelso Delos Reyes (User ID 47)
    'CHRISTOPHER CATAPANG': 48,     # Reymark Lejano (User ID 48)
}

VEHICLE_RATES = {
    14: 1699.0, # Vios J MT (NCX 4117)
    16: 1999.0, # Vios (DBA 6730)
    17: 2000.0, # Vios XE AT (DAT 1396)
    18: 2000.0, # Vios XLE AT (DBJ 9483)
    22: 2199.0, # Honda City (DCF 2987)
    23: 2600.0, # Honda BR-V (NID 2724)
    26: 3000.0, # Innova XE AT (NHN 5388)
    27: 3000.0, # Innova XE AT (CCK 1126)
    34: 3999.0, # Hiace (NCW 3918)
    30: 4000.0  # Fortuner (DBH 8812)
}

PLATE_MAP = {
    '4117': 14, '6730': 16, '1396': 17, '9483': 18, '2987': 22,
    '2724': 23, '5388': 26, '1126': 27, '3918': 34, '8812': 30, '2182': 18
}

def match_vehicle(car_str):
    if not car_str: return 17
    s = str(car_str).upper()
    for plate, vid in PLATE_MAP.items():
        if plate in s: return vid
    if 'BRV' in s or 'BR-V' in s: return 23
    if 'HIACE' in s: return 34
    if 'INNOVA' in s: return 26
    if 'VIOS' in s: return 17
    return 17

def normalize_name(name):
    if not name: return ""
    s = re.sub(r'[^A-Za-z0-9\s]', ' ', str(name)).upper()
    tokens = [t for t in s.split() if t not in ['SPC', 'TAN', 'TNN', 'DP', 'PAID', 'BAL', 'BALANCE', 'HRS', 'RENTAL']]
    if not tokens: return str(name).strip().upper()
    
    joined = ' '.join(tokens)
    if 'HUBERT' in tokens or 'HUBBERT' in tokens:
        return 'HUBERT SANCHEZ'
    if 'MARJORIE' in tokens and 'ISLETA' in tokens:
        return 'MARJORIE ISLETA'
    if 'JOSE' in tokens or ('SANTOS' in tokens and ('JOSE' in tokens or 'MARIE' in tokens)):
        return 'JOSE MARIE SANTOS'
    if 'MARJHERIE' in tokens or ('CATAPANG' in tokens and 'BERENA' in tokens):
        return 'MARJHERIE CATAPANG'
    if 'HARMAN' in tokens:
        return 'HARMAN BHULLAR'
    if 'ARVIN' in tokens and ('CORPUZ' in tokens or 'CORPOZ' in tokens):
        return 'ARVIN CORPUZ'
    if 'JEAN' in tokens and 'ALOR' in tokens:
        return 'JEAN ALOR'
    if 'CHRISTOPHER' in tokens and 'CATAPANG' in tokens:
        return 'CHRISTOPHER CATAPANG'
    if 'CHERRYLYN' in tokens:
        return 'CHERRYLYN GARDIOLA'
    if 'JOMAR' in tokens and 'GELI' in tokens:
        return 'JOMAR GELI'
    if 'DAPAT' in tokens or 'ALLAN SALVADOR' in joined:
        return 'LAN DAPAT'
    if 'GAMARO' in tokens:
        return 'NORBERT GAMARO'
    if 'ALEXANDER' in tokens and 'ARAMIL' in tokens:
        return 'ALEXANDER ARAMIL'
    if 'MICHAEL' in tokens and 'VINCENT' in tokens:
        return 'MICHAEL VINCENT'
    if 'CECILLE' in tokens and 'VALENCIA' in tokens:
        return 'CECILLE VALENCIA'
    if 'ALLIANA' in tokens and 'TOLENTINO' in tokens:
        return 'ALLIANA TOLENTINO'
    if 'THERESA' in tokens and 'PANGILINAN' in tokens:
        return 'THERESA PANGILINAN'
    if 'DANE' in tokens and 'MARIONNE' in tokens:
        return 'DANE MARIONNE'
        
    return ' '.join(tokens[:2]) if len(tokens) >= 2 else tokens[0]

def format_title_name(raw_name, norm_name):
    clean = re.sub(r'[^A-Za-z0-9\s\.\-\']', ' ', str(raw_name)).strip()
    words = [w for w in clean.split() if w.upper() not in ['SPC', 'TAN', 'TNN', 'DP', 'PAID', 'BAL', 'BALANCE', 'HRS', 'RENTAL']]
    if words:
        res = ' '.join(w.capitalize() if w.isupper() else w for w in words)
        return res
    return norm_name.title()

car_make_rows = []
for r in range(1, sheet.max_row + 1):
    row_vals = [sheet.cell(row=r, column=c).value for c in range(1, 15)]
    if any(isinstance(v, str) and 'CAR MAKE' in v.upper() for v in row_vals if v):
        car_make_rows.append(r)

MONTH_INFO = {
    1: (2025, 4), 8: (2025, 5), 15: (2025, 6), 26: (2025, 7),
    49: (2026, 1), 59: (2026, 2), 69: (2026, 3), 79: (2026, 4),
    92: (2026, 5), 105: (2026, 6), 116: (2026, 7), 129: (2026, 8),
    142: (2026, 9), 155: (2026, 10), 168: (2026, 11)
}

all_parsed = []
for idx, r in enumerate(car_make_rows):
    year, month = MONTH_INFO.get(r, (2026, 1))
    days_row = None
    for tr in [r+1, r+2, r+3]:
        if tr <= sheet.max_row:
            ints = [sheet.cell(row=tr, column=c).value for c in range(4, 25)]
            if sum(1 for x in ints if isinstance(x, int)) >= 3:
                days_row = tr
                break
    if not days_row: continue
    
    col_to_day = {}
    current_day = 1
    for c in range(4, sheet.max_column + 1):
        v = sheet.cell(row=days_row, column=c).value
        if isinstance(v, int):
            current_day = v
        elif v is not None and str(v).strip().isdigit():
            current_day = int(str(v).strip())
        col_to_day[c] = current_day
        
    next_r = car_make_rows[idx+1] if idx+1 < len(car_make_rows) else (r + 15)
    
    for vr in range(days_row + 1, next_r):
        veh_str = sheet.cell(row=vr, column=1).value or sheet.cell(row=vr, column=2).value
        if not veh_str or any(k in str(veh_str).upper() for k in ['TOTAL', 'SALES', 'CAR MAKE']):
            continue
        veh_id = match_vehicle(veh_str)
        
        c = 4
        while c <= 72:
            cell = sheet.cell(row=vr, column=c)
            val = cell.value
            comm = cell.comment
            fill = cell.fill.start_color.rgb if cell.fill and cell.fill.start_color else None
            is_colored = fill and fill not in ('00000000', 'FFFFFFFF', '0', None)
            
            has_name = bool(val and str(val).strip() and not str(val).strip().isdigit())
            has_comm = bool(comm and any(k in comm.text for k in ['Name:', 'Contact', 'SPC', 'TAN', 'PAID', 'rent', 'hrs']))
            
            if has_name or (has_comm and is_colored):
                cust_name = str(val).strip() if has_name else ''
                comm_text = comm.text if comm else ''
                if not cust_name and 'Name:' in comm_text:
                    m = re.search(r'Name:\s*([^\n\r]+)', comm_text, re.IGNORECASE)
                    if m: cust_name = m.group(1).strip()
                    
                start_col = c
                start_day = col_to_day.get(c, 1)
                booking_fill = fill
                
                end_col = c
                scan_c = c + 1
                while scan_c <= 72:
                    scell = sheet.cell(row=vr, column=scan_c)
                    sval = scell.value
                    sfill = scell.fill.start_color.rgb if scell.fill and scell.fill.start_color else None
                    if sval and str(sval).strip() and not str(sval).strip().isdigit() and str(sval).strip() != cust_name:
                        break
                    if sfill == booking_fill and is_colored:
                        end_col = scan_c
                        if not comm_text and scell.comment: comm_text = scell.comment.text
                        scan_c += 1
                    elif not is_colored and sval == val:
                        end_col = scan_c
                        scan_c += 1
                    else:
                        break
                        
                end_day = col_to_day.get(end_col, start_day)
                if end_day < start_day: end_day = start_day
                days_count = max(1, end_day - start_day + 1)
                
                if cust_name and cust_name.upper() not in ['PICK-UP', 'DROP-OFF', 'MAINTENANCE', 'AVAILABLE']:
                    norm = normalize_name(cust_name)
                    formatted_name = format_title_name(cust_name, norm)
                    try:
                        start_dt = date(year, month, start_day)
                        end_dt = start_dt + timedelta(days=days_count)
                    except ValueError:
                        start_dt = date(year, month, min(start_day, 28))
                        end_dt = start_dt + timedelta(days=days_count)
                        
                    daily_rate = VEHICLE_RATES.get(veh_id, 2000.0)
                    total_price = daily_rate * days_count
                    
                    is_cancelled = False
                    check_str = f"{cust_name} {comm_text}".upper()
                    if any(k in check_str for k in ['CANCEL', 'CANCELLED', 'VOID', 'CANCELED']):
                        is_cancelled = True
                        
                    today_dt = date(2026, 10, 1)
                    if is_cancelled:
                        status = 'Cancelled'
                    elif end_dt < today_dt:
                        status = 'Completed'
                    elif start_dt <= today_dt <= end_dt:
                        status = 'Picked Up'
                    else:
                        status = 'Confirmed'
                        
                    pts = int(total_price // 100) if status == 'Completed' else 0
                    
                    all_parsed.append({
                        'raw_name': cust_name,
                        'norm_name': norm,
                        'formatted_name': formatted_name,
                        'vehicle_id': veh_id,
                        'start_date': start_dt.isoformat(),
                        'end_date': end_dt.isoformat(),
                        'days': days_count,
                        'daily_rate': daily_rate,
                        'total_price': total_price,
                        'status': status,
                        'points_earned': pts,
                        'is_verified_customer': norm in VERIFIED_MAP,
                        'assigned_verified_uid': VERIFIED_MAP.get(norm, None)
                    })
                c = end_col + 1
            else:
                c += 1

print(f"Total parsed bookings: {len(all_parsed)}")

def execute_migration():
    conn = psycopg2.connect(SUPABASE_DB_URL)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        print("\n1. Ensuring schema compatibility...")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS customer_name VARCHAR(150);")
        cur.execute("ALTER TABLE users ALTER COLUMN email DROP NOT NULL;")
        
        # 2. Fetch existing verified users
        cur.execute("SELECT id, full_name, email FROM users WHERE id IN %s", (tuple(VERIFIED_MAP.values()),))
        verified_users = {r['id']: r for r in cur.fetchall()}
        print(f"Found {len(verified_users)} verified users in DB.")
        
        # 3. Handle non-verified past customers
        print("\n2. Processing non-verified past customers...")
        # Gather unique non-verified customers
        non_verified_groups = defaultdict(list)
        for b in all_parsed:
            if not b['is_verified_customer']:
                non_verified_groups[b['norm_name']].append(b)
                
        print(f"Unique non-verified past customers: {len(non_verified_groups)}")
        
        # Check existing non-email users
        cur.execute("SELECT id, full_name, first_name, last_name FROM users WHERE email IS NULL")
        existing_non_email = {r['full_name'].upper(): r['id'] for r in cur.fetchall()}
        
        cust_to_uid = {}
        for norm_name, b_list in non_verified_groups.items():
            first_b = b_list[0]
            fmt_name = first_b['formatted_name']
            
            # Check if user already exists
            if fmt_name.upper() in existing_non_email:
                uid = existing_non_email[fmt_name.upper()]
            elif norm_name in existing_non_email:
                uid = existing_non_email[norm_name]
            else:
                tokens = fmt_name.split()
                fname = tokens[0]
                lname = ' '.join(tokens[1:]) if len(tokens) > 1 else 'Customer'
                
                # Earliest booking date as created_at
                earliest_date = min(b['start_date'] for b in b_list)
                created_at_dt = f"{earliest_date} 08:00:00+08"
                
                cur.execute("""
                    INSERT INTO users (
                        first_name, last_name, email, role,
                        is_verified, is_regular_customer, loyalty_points, created_at
                    ) VALUES (
                        %s, %s, NULL, 'customer',
                        0, FALSE, 0, %s
                    ) RETURNING id
                """, (fname, lname, created_at_dt))
                uid = cur.fetchone()['id']
                # Sync user_id column if needed
                cur.execute("UPDATE users SET user_id = id WHERE id = %s AND (user_id IS NULL OR user_id != id)", (uid,))
                existing_non_email[fmt_name.upper()] = uid
                
            cust_to_uid[norm_name] = uid
            
        print(f"All {len(cust_to_uid)} non-verified customer accounts prepared.")
        
        # 4. Clean out old imported bookings (preserve booking #341)
        print("\n3. Cleaning old imported bookings (preserving #341)...")
        cur.execute("DELETE FROM booking_return_reminders WHERE booking_id != 341")
        cur.execute("DELETE FROM payments WHERE booking_id != 341")
        cur.execute("DELETE FROM reviews WHERE booking_id != 341")
        cur.execute("DELETE FROM bookings WHERE id != 341")
        print("Old imported bookings, payments, reminders cleared.")
        
        # 5. Insert all parsed bookings
        print("\n4. Inserting clean realigned bookings...")
        inserted_count = 0
        payment_count = 0
        
        # Sort chronologically by start_date
        all_parsed.sort(key=lambda x: (x['start_date'], x['vehicle_id']))
        
        for idx, b in enumerate(all_parsed, 1):
            if b['is_verified_customer']:
                target_uid = b['assigned_verified_uid']
                cust_name = verified_users[target_uid]['full_name']
            else:
                target_uid = cust_to_uid[b['norm_name']]
                cust_name = b['formatted_name']
                
            start_d = b['start_date']
            end_d = b['end_date']
            tot_p = b['total_price']
            status = b['status']
            pts = b['points_earned']
            
            # Booking created_at
            try:
                s_dt = datetime.strptime(start_d, '%Y-%m-%d')
                c_dt = s_dt - timedelta(days=1)
                created_at_str = c_dt.strftime('%Y-%m-%d 10:00:00+08')
            except Exception:
                created_at_str = f"{start_d} 00:00:00+08"
                
            completed_at_str = f"{end_d} 18:00:00+08" if status == 'Completed' else None
            pay_status = 'Cancelled' if status == 'Cancelled' else 'Fully Paid'
            amt_paid = tot_p if status != 'Cancelled' else 0.0
            bal_amt = 0.0
            
            ref_num = f"BK-{start_d.replace('-', '')}-{idx:04d}"
            
            cur.execute("""
                INSERT INTO bookings (
                    user_id, vehicle_id, customer_name, start_date, end_date,
                    total_price, base_price, amount_paid, balance_amount,
                    status, payment_status, payment_type, payment_method,
                    points_earned, points_redeemed,
                    pickup_location, rental_type, destination, rental_purpose,
                    start_time, end_time, reference_num, created_at, completed_at
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, 'Full', 'GCash',
                    %s, 0,
                    'Main Hub, Calamba, Laguna', 'Self Drive', 'Calabarzon / Metro Manila', 'Personal / Business Rental',
                    '09:00', '18:00', %s, %s, %s
                ) RETURNING id
            """, (
                target_uid, b['vehicle_id'], cust_name, start_d, end_d,
                tot_p, tot_p, amt_paid, bal_amt,
                status, pay_status,
                pts,
                ref_num, created_at_str, completed_at_str
            ))
            b_id = cur.fetchone()['id']
            # Sync booking_id with id
            cur.execute("UPDATE bookings SET booking_id = id WHERE id = %s", (b_id,))
            inserted_count += 1
            
            # Record payment for completed/confirmed bookings
            if amt_paid > 0:
                cur.execute("""
                    INSERT INTO payments (
                        booking_id, amount, method, reference_number, status
                    ) VALUES (
                        %s, %s, 'GCash', %s, 'completed'
                    )
                """, (b_id, amt_paid, f"PAY-{ref_num}"))
                payment_count += 1
                
        print(f"Inserted {inserted_count} bookings and {payment_count} payments.")
        
        # 6. Recalculate Loyalty Points and Total Spent for all users
        print("\n5. Recalculating user stats (loyalty_points, total_spent, regular customer)...")
        cur.execute("""
            UPDATE users u
            SET 
                loyalty_points = COALESCE(b_stats.total_pts, 0),
                is_regular_customer = (COALESCE(b_stats.comp_count, 0) >= 3 OR COALESCE(u.regular_customer_manual, FALSE))
            FROM (
                SELECT 
                    user_id,
                    COUNT(*) FILTER (WHERE status = 'Completed') AS comp_count,
                    COALESCE(SUM(points_earned) FILTER (WHERE status = 'Completed'), 0) AS total_pts
                FROM bookings
                GROUP BY user_id
            ) b_stats
            WHERE u.id = b_stats.user_id;
        """)
        
        # Also reset points to 0 for users with no bookings
        cur.execute("""
            UPDATE users u
            SET loyalty_points = 0
            WHERE id NOT IN (SELECT DISTINCT user_id FROM bookings WHERE status = 'Completed');
        """)
        
        conn.commit()
        print("\n=== TRANSACTION COMMITTED SUCCESSFULLY! ===")
        
        # 7. Verification checks
        print("\n6. VERIFICATION CHECKS:")
        
        # 16 Verified Users Check
        print("\n--- 16 VERIFIED USERS ---")
        cur.execute("""
            SELECT u.id, u.full_name, u.email, u.loyalty_points, u.is_regular_customer,
                   COUNT(b.id) AS total_bookings,
                   COUNT(b.id) FILTER (WHERE b.status = 'Completed') AS completed_bookings,
                   COALESCE(SUM(b.total_price), 0) AS total_spent
            FROM users u
            LEFT JOIN bookings b ON u.id = b.user_id
            WHERE u.id IN %s
            GROUP BY u.id, u.full_name, u.email, u.loyalty_points, u.is_regular_customer
            ORDER BY u.id
        """, (tuple(VERIFIED_MAP.values()),))
        
        for r in cur.fetchall():
            vip = "[VIP]" if r['is_regular_customer'] else ""
            print(f"User {r['id']:02d}: {r['full_name']} | Pts: {r['loyalty_points']} | Spent: ₱{r['total_spent']:,.2f} | Bookings: {r['total_bookings']} (Comp: {r['completed_bookings']}) {vip}")
            
        # Check Arvin Corpuz bookings (User ID 25)
        print("\n--- User 25 (Arvin Corpuz) Bookings ---")
        cur.execute("SELECT id, vehicle_id, start_date, end_date, total_price, status, customer_name FROM bookings WHERE user_id = 25 ORDER BY start_date")
        for b in cur.fetchall():
            print(f"  #{b['id']}: {b['start_date']} to {b['end_date']} | Veh {b['vehicle_id']} | ₱{b['total_price']:,.2f} | {b['status']} | {b['customer_name']}")

        # Check Hubert Sanchez bookings (User ID 28)
        print("\n--- User 28 (Hubert Sanchez) Bookings ---")
        cur.execute("SELECT id, vehicle_id, start_date, end_date, total_price, status, customer_name FROM bookings WHERE user_id = 28 ORDER BY start_date")
        for b in cur.fetchall():
            print(f"  #{b['id']}: {b['start_date']} to {b['end_date']} | Veh {b['vehicle_id']} | ₱{b['total_price']:,.2f} | {b['status']} | {b['customer_name']}")

        # Check Booking 341 (User 52)
        print("\n--- Booking 341 (Preserved live test booking) ---")
        cur.execute("SELECT id, user_id, vehicle_id, start_date, total_price, status FROM bookings WHERE id = 341")
        print(f"  Booking 341: {cur.fetchone()}")

        # Check total bookings in DB
        cur.execute("SELECT COUNT(*) FROM bookings")
        print(f"\nTotal bookings in DB now: {cur.fetchone()['count']}")
        
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    execute_migration()
