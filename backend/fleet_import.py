# ==============================================================================
# FLEET CALENDAR EXCEL IMPORT & SMART RENTER MATCHING ENGINE
# Supports ARC-MONITORING Gantt sheets & standard tabular booking lists
# ==============================================================================
import os
import re
import datetime
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

def parse_fleet_excel_file(file_stream_or_path):
    """
    Parses an uploaded Excel workbook (file path, file object, or BytesIO).
    Automatically detects if the sheet is an ARC-MONITORING Gantt style calendar
    or a standard tabular list, and extracts uniform booking records.
    """
    if isinstance(file_stream_or_path, (str, bytes, os.PathLike)):
        wb = openpyxl.load_workbook(file_stream_or_path, data_only=True)
    else:
        wb = openpyxl.load_workbook(io.BytesIO(file_stream_or_path.read()), data_only=True)

    sheet = wb.active
    
    # Check if first few rows indicate a standard tabular list
    # Look for headers like: 'Vehicle', 'Plate', 'Customer', 'Start Date', 'End Date'
    is_tabular = False
    tabular_header_row = -1
    col_mapping = {}
    
    for r in range(1, min(10, sheet.max_row + 1)):
        row_vals = [str(sheet.cell(r, c).value or '').strip().lower() for c in range(1, min(20, sheet.max_column + 1))]
        has_veh = any('veh' in v or 'car' in v or 'plate' in v for v in row_vals)
        has_cust = any('cust' in v or 'renter' in v or 'client' in v or 'name' in v for v in row_vals)
        has_date = any('start' in v or 'date' in v or 'pickup' in v for v in row_vals)
        if has_veh and has_cust and has_date:
            is_tabular = True
            tabular_header_row = r
            for c_idx, val in enumerate(row_vals, 1):
                if 'veh' in val or 'car' in val or 'model' in val:
                    col_mapping.setdefault('vehicle', c_idx)
                if 'plate' in val:
                    col_mapping['plate'] = c_idx
                if 'cust' in val or 'renter' in val or 'client' in val or 'name' in val:
                    col_mapping.setdefault('customer', c_idx)
                if 'phone' in val or 'mobile' in val or 'contact' in val:
                    col_mapping['phone'] = c_idx
                if 'email' in val:
                    col_mapping['email'] = c_idx
                if 'start' in val or 'pickup' in val or 'from' in val:
                    col_mapping.setdefault('start_date', c_idx)
                if 'end' in val or 'return' in val or 'to' in val or 'drop' in val:
                    col_mapping.setdefault('end_date', c_idx)
                if 'price' in val or 'rate' in val or 'total' in val or 'amount' in val:
                    col_mapping.setdefault('total_price', c_idx)
                if 'paid' in val:
                    col_mapping.setdefault('amount_paid', c_idx)
                if 'status' in val:
                    col_mapping.setdefault('status', c_idx)
            break

    if is_tabular and 'vehicle' in col_mapping and 'customer' in col_mapping and 'start_date' in col_mapping:
        return _parse_tabular_sheet(sheet, tabular_header_row, col_mapping)
    else:
        # Parse as ARC-MONITORING calendar/Gantt style grid
        return _parse_arc_gantt_sheet(sheet)


def _parse_tabular_sheet(sheet, header_row, col_map):
    raw_records = []
    for r in range(header_row + 1, sheet.max_row + 1):
        veh_val = sheet.cell(r, col_map['vehicle']).value
        cust_val = sheet.cell(r, col_map['customer']).value
        start_val = sheet.cell(r, col_map['start_date']).value
        if not veh_val or not cust_val or not start_val:
            continue
            
        veh_str = str(veh_val).strip()
        plate_str = str(sheet.cell(r, col_map.get('plate', col_map['vehicle'])).value or '').strip()
        cust_str = str(cust_val).strip()
        
        # Parse dates
        start_str = _format_date(start_val)
        end_val = sheet.cell(r, col_map.get('end_date', col_map['start_date'])).value or start_val
        end_str = _format_date(end_val)
        
        if not start_str or not end_str:
            continue
            
        phone = str(sheet.cell(r, col_map['phone']).value or '').strip() if 'phone' in col_map else ''
        email = str(sheet.cell(r, col_map['email']).value or '').strip() if 'email' in col_map else ''
        
        total_price = _parse_number(sheet.cell(r, col_map['total_price']).value) if 'total_price' in col_map else None
        amount_paid = _parse_number(sheet.cell(r, col_map['amount_paid']).value) if 'amount_paid' in col_map else None
        status = str(sheet.cell(r, col_map['status']).value or '').strip() if 'status' in col_map else ''
        
        raw_records.append({
            'vehicle_raw': veh_str,
            'plate_raw': plate_str,
            'customer_name': cust_str,
            'customer_phone': phone,
            'customer_email': email,
            'start_date': start_str,
            'end_date': end_str,
            'total_price': total_price,
            'amount_paid': amount_paid,
            'status_raw': status,
            'source_format': 'tabular'
        })
    return raw_records


def _parse_arc_gantt_sheet(sheet):
    """
    Parses multi-month calendar grids like ARC-MONITORING-2026.xlsx.
    Pre-fills merged cells and extracts contiguous customer booking segments.
    """
    # 1. Pre-fill merged cells map
    merged_map = {}
    for mr in list(sheet.merged_cells.ranges):
        top_val = sheet.cell(mr.min_row, mr.min_col).value
        for r in range(mr.min_row, mr.max_row + 1):
            for c in range(mr.min_col, mr.max_col + 1):
                merged_map[(r, c)] = top_val

    raw_records = []
    current_month_date = None
    day_cols = {} # column index -> int day number

    # Status / blackout keyword filter (names that are not customer names)
    non_customer_keywords = {
        'CAR MAKE', 'PICK-UP', 'PICKUP', 'DROP-OFF', 'DROPOFF', 'OFF',
        'MAINTENANCE', 'REPAIR', 'AVAILABLE', 'RESERVED', 'INSPECTION',
        'CLEANING', 'PULL OUT', 'PULL-OUT', 'TOTAL', 'RATE', 'SALES',
        'NONE', 'N/A', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN', 'MON'
    }

    for r in range(1, sheet.max_row + 1):
        cell_a = sheet.cell(r, 1).value
        cell_a_str = str(cell_a or '').strip().upper()

        # Check if row defines Month header
        if 'CAR MAKE' in cell_a_str:
            current_month_date = None
            day_cols = {}
            for c in range(2, min(35, sheet.max_column + 1)):
                val = sheet.cell(r, c).value
                if isinstance(val, (datetime.datetime, datetime.date)):
                    current_month_date = datetime.date(val.year, val.month, 1)
                    break
                elif val and isinstance(val, str):
                    val_clean = val.strip().upper()
                    if 'ARP' in val_clean: val_clean = val_clean.replace('ARP', 'APR')
                    match = re.search(r'([A-Z]+)\s*(\d{4})', val_clean)
                    if match:
                        m_str, y_str = match.groups()
                        months = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']
                        for m_idx, m_name in enumerate(months, 1):
                            if m_name.startswith(m_str[:3]):
                                current_month_date = datetime.date(int(y_str), m_idx, 1)
                                break
                        if current_month_date:
                            break
            continue

        # Check if row defines day numbers 1, 2, 3...
        first_few = [sheet.cell(r, c).value for c in range(2, 10)]
        if any(v == 1 for v in first_few):
            day_cols = {}
            for c in range(2, sheet.max_column + 1):
                val = sheet.cell(r, c).value
                if isinstance(val, int) and 1 <= val <= 31:
                    day_cols[c] = val
            continue

        # If we have a vehicle row
        if cell_a and isinstance(cell_a, str) and day_cols and current_month_date:
            veh_name = cell_a.strip()
            # Ignore summary headers
            if any(k in veh_name.upper() for k in ['SALES', 'RATE', 'TOTAL', 'EXPENSES', 'SUMMARY', 'CAR MAKE']):
                continue

            current_cust = None
            start_day = None
            last_day = None

            for c in sorted(day_cols.keys()):
                day_num = day_cols[c]
                # Get cell value considering merged cells
                val = merged_map.get((r, c), sheet.cell(r, c).value)
                val_str = str(val or '').strip()

                is_valid_customer = (
                    bool(val_str) and
                    val_str.upper() not in non_customer_keywords and
                    not val_str.isdigit() and
                    len(val_str) > 2
                )

                if is_valid_customer:
                    if current_cust and val_str.upper() == current_cust.upper():
                        last_day = day_num
                    else:
                        # Flush previous booking
                        if current_cust and start_day and last_day:
                            raw_records.append({
                                'vehicle_raw': veh_name,
                                'plate_raw': veh_name,
                                'customer_name': current_cust,
                                'customer_phone': '',
                                'customer_email': '',
                                'start_date': f"{current_month_date.year}-{current_month_date.month:02d}-{start_day:02d}",
                                'end_date': f"{current_month_date.year}-{current_month_date.month:02d}-{last_day:02d}",
                                'total_price': None,
                                'amount_paid': None,
                                'source_format': 'arc_gantt'
                            })
                        current_cust = val_str
                        start_day = day_num
                        last_day = day_num
                else:
                    if current_cust and start_day and last_day:
                        raw_records.append({
                            'vehicle_raw': veh_name,
                            'plate_raw': veh_name,
                            'customer_name': current_cust,
                            'customer_phone': '',
                            'customer_email': '',
                            'start_date': f"{current_month_date.year}-{current_month_date.month:02d}-{start_day:02d}",
                            'end_date': f"{current_month_date.year}-{current_month_date.month:02d}-{last_day:02d}",
                            'total_price': None,
                            'amount_paid': None,
                            'source_format': 'arc_gantt'
                        })
                        current_cust = None
                        start_day = None
                        last_day = None

            if current_cust and start_day and last_day:
                raw_records.append({
                    'vehicle_raw': veh_name,
                    'plate_raw': veh_name,
                    'customer_name': current_cust,
                    'customer_phone': '',
                    'customer_email': '',
                    'start_date': f"{current_month_date.year}-{current_month_date.month:02d}-{start_day:02d}",
                    'end_date': f"{current_month_date.year}-{current_month_date.month:02d}-{last_day:02d}",
                    'total_price': None,
                    'amount_paid': None,
                    'source_format': 'arc_gantt'
                })

    return raw_records


def _format_date(val):
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.strftime('%Y-%m-%d')
    if isinstance(val, str):
        val = val.strip()
        m = re.match(r'^(\d{4})[-/](\d{1,2})[-/](\d{1,2})', val)
        if m:
            y, mth, d = m.groups()
            return f"{y}-{int(mth):02d}-{int(d):02d}"
    return None


def _parse_number(val):
    if val is None: return None
    if isinstance(val, (int, float)): return float(val)
    s = re.sub(r'[^\d.]', '', str(val))
    try:
        return float(s) if s else None
    except ValueError:
        return None


def match_and_validate_import_records(raw_records, cur):
    """
    Enriches raw extracted records with:
    1. Vehicle matching (by plate number and model)
    2. Smart Renter matching (by exact or fuzzy name, phone, email)
    3. Pricing calculation
    4. Overlap/conflict detection with existing bookings
    """
    # 1. Fetch all system vehicles
    cur.execute("SELECT id, brand, model, plate_number, daily_rate, status FROM vehicles ORDER BY id ASC")
    db_vehicles = [dict(v) for v in cur.fetchall()]

    # 2. Fetch all system users (renters)
    cur.execute("""
        SELECT u.id, u.full_name, u.email, u.phone, u.role,
               COUNT(b.id) AS total_past_rentals
        FROM users u
        LEFT JOIN bookings b ON u.id = b.user_id AND b.status != 'cancelled'
        GROUP BY u.id, u.full_name, u.email, u.phone, u.role
    """)
    db_users = [dict(u) for u in cur.fetchall()]

    # Build fast normalized lookup maps
    user_name_map = {}
    for u in db_users:
        if u.get('full_name'):
            norm = _normalize_name(u['full_name'])
            user_name_map[norm] = u

    # 3. Fetch existing bookings for conflict check
    cur.execute("""
        SELECT id, vehicle_id, start_date, end_date, status, customer_name
        FROM bookings
        WHERE status NOT IN ('cancelled', 'rejected', 'deleted')
    """)
    existing_bookings = [dict(b) for b in cur.fetchall()]

    enriched = []
    summary = {
        'total_records': len(raw_records),
        'matched_vehicles': 0,
        'unmatched_vehicles': 0,
        'matched_renters': 0,
        'new_renters': 0,
        'conflicts': 0
    }

    unique_matched_vehicles = set()
    seen_names = set()

    for idx, r in enumerate(raw_records, 1):
        veh_str = r['vehicle_raw']
        cust_str = r['customer_name']
        start_d = r['start_date']
        end_d = r['end_date']

        # --- A. VEHICLE MATCHING ---
        matched_veh = _find_best_vehicle_match(veh_str, r.get('plate_raw', ''), db_vehicles)
        if matched_veh:
            unique_matched_vehicles.add(matched_veh['id'])

        # --- B. RENTER MATCHING (Smart Account Identification) ---
        norm_cust = _normalize_name(cust_str)
        matched_user = user_name_map.get(norm_cust)

        # Secondary search if not exact match: check if first + last matches
        if not matched_user:
            cust_tokens = set(norm_cust.split())
            if len(cust_tokens) >= 2:
                for db_norm, u_obj in user_name_map.items():
                    u_tokens = set(db_norm.split())
                    # If all tokens match or Jaccard similarity is high
                    overlap = cust_tokens.intersection(u_tokens)
                    if len(overlap) >= 2 and len(overlap) >= min(len(cust_tokens), len(u_tokens)):
                        matched_user = u_obj
                        break

        # --- C. PRICING & DURATION ---
        start_dt = datetime.datetime.strptime(start_d, '%Y-%m-%d').date()
        end_dt = datetime.datetime.strptime(end_d, '%Y-%m-%d').date()
        days_count = max(1, (end_dt - start_dt).days + 1)

        daily_rate = float(matched_veh['daily_rate'] if matched_veh else 2000)
        total_price = r.get('total_price')
        if total_price is None or total_price <= 0:
            total_price = daily_rate * days_count
        else:
            total_price = float(total_price)

        amount_paid = float(r.get('amount_paid') or 0.0)
        balance = max(0.0, total_price - amount_paid)
        payment_status = 'Paid' if (balance == 0 and total_price > 0) else ('Partially Paid' if amount_paid > 0 else 'Unpaid')

        # --- D. CONFLICT CHECKING ---
        has_conflict = False
        conflict_with = None
        if matched_veh:
            v_id = matched_veh['id']
            for eb in existing_bookings:
                if eb['vehicle_id'] == v_id:
                    eb_s = eb['start_date'] if isinstance(eb['start_date'], datetime.date) else datetime.datetime.strptime(str(eb['start_date'])[:10], '%Y-%m-%d').date()
                    eb_e = eb['end_date'] if isinstance(eb['end_date'], datetime.date) else datetime.datetime.strptime(str(eb['end_date'])[:10], '%Y-%m-%d').date()
                    if not (end_dt < eb_s or start_dt > eb_e):
                        has_conflict = True
                        conflict_with = f"Booking #{eb['id']} ({eb.get('customer_name') or 'Customer'}): {eb_s} to {eb_e}"
                        break

        if has_conflict:
            summary['conflicts'] += 1

        is_existing_user = bool(matched_user)
        user_match_status = 'existing_user' if is_existing_user else ('repeat_in_excel' if norm_cust in seen_names else 'new_user')
        if not is_existing_user:
            seen_names.add(norm_cust)

        if is_existing_user:
            summary['matched_renters'] += 1
        else:
            summary['new_renters'] += 1

        veh_id = matched_veh['id'] if matched_veh else None
        veh_name = f"{matched_veh['brand']} {matched_veh['model']}" if matched_veh else veh_str
        plate_no = matched_veh['plate_number'] if matched_veh else ''
        cal_color = matched_veh.get('calendar_color') if matched_veh else '#00B14F'

        user_id = matched_user['id'] if matched_user else None

        matched_user_obj = {
            'id': user_id,
            'full_name': matched_user['full_name'] if matched_user else cust_str,
            'email': matched_user.get('email') if matched_user else '',
            'phone': matched_user.get('phone') if matched_user else (r.get('customer_phone') or ''),
            'total_past_rentals': matched_user.get('total_past_rentals', 0) if matched_user else 0,
            'is_existing': is_existing_user
        }

        enriched.append({
            'import_id': idx,
            'vehicle_id': veh_id,
            'vehicle_name': veh_name,
            'plate_number': plate_no,
            'calendar_color': cal_color,
            'vehicle_raw': veh_str,
            'matched_vehicle': matched_veh,
            'customer_name': cust_str,
            'matched_user': matched_user_obj,
            'matched_user_id': user_id,
            'user_match_status': user_match_status,
            'is_existing_user': is_existing_user,
            'start_date': start_d,
            'end_date': end_d,
            'days_count': days_count,
            'total_days': days_count,
            'daily_rate': daily_rate,
            'total_price': total_price,
            'amount_paid': amount_paid,
            'balance_amount': balance,
            'payment_status': payment_status,
            'is_conflict': has_conflict,
            'has_conflict': has_conflict,
            'conflict_reason': conflict_with,
            'conflict_details': conflict_with,
            'source_format': r.get('source_format', 'excel')
        })

    summary['matched_vehicles'] = len(unique_matched_vehicles)
    summary['cars_matched'] = summary['matched_vehicles']
    summary['cars_unmatched'] = summary['unmatched_vehicles']
    summary['existing_renters_matched'] = summary['matched_renters']
    summary['new_renters_to_create'] = summary['new_renters']

    return {
        'summary': summary,
        'records': enriched
    }


def _normalize_name(name):
    if not name: return ""
    s = str(name).strip().lower()
    s = re.sub(r'[^a-z0-9\s]', '', s)
    return " ".join(s.split())


def _find_best_vehicle_match(veh_raw, plate_raw, db_vehicles):
    """
    Finds the best matching vehicle by extracting plate characters
    or brand/model keywords.
    """
    target = f"{veh_raw} {plate_raw}".upper()
    target_clean = re.sub(r'[^A-Z0-9]', '', target)

    # 1. Exact plate match (ignoring spaces/dashes)
    for v in db_vehicles:
        plate = str(v.get('plate_number') or '').upper()
        plate_clean = re.sub(r'[^A-Z0-9]', '', plate)
        if plate_clean and plate_clean in target_clean:
            return {
                'id': v['id'],
                'brand': v['brand'],
                'model': v['model'],
                'plate_number': v['plate_number'],
                'daily_rate': float(v['daily_rate'] or 0)
            }

    # 2. Match by individual plate tokens (e.g. 'NCX 4117' -> 'NCX' and '4117')
    for v in db_vehicles:
        plate = str(v.get('plate_number') or '').upper().strip()
        parts = plate.split()
        if len(parts) >= 2:
            if parts[0] in target and parts[1] in target:
                return {
                    'id': v['id'],
                    'brand': v['brand'],
                    'model': v['model'],
                    'plate_number': v['plate_number'],
                    'daily_rate': float(v['daily_rate'] or 0)
                }

    # 3. Model keyword match
    for v in db_vehicles:
        model = str(v.get('model') or '').upper()
        if model and model in target:
            return {
                'id': v['id'],
                'brand': v['brand'],
                'model': v['model'],
                'plate_number': v['plate_number'],
                'daily_rate': float(v['daily_rate'] or 0)
            }

    return None


def execute_import_to_database(records_to_import, auto_create_renters, cur, commit_fn, admin_id=1):
    """
    Saves validated records to the PostgreSQL database.
    Creates renter accounts for new users if requested.
    Returns counts of inserted bookings and created renter profiles.
    """
    today = datetime.date.today()
    created_renters_count = 0
    imported_bookings_count = 0

    # In-memory registry of newly created users during this batch
    # to link repeat bookings of the same new customer to 1 account
    new_users_batch = {}

    for r in records_to_import:
        vehicle_id = r.get('vehicle_id') or (r.get('matched_vehicle') or {}).get('id')
        if not vehicle_id:
            continue

        cust_name = str(r.get('customer_name') or 'Customer').strip()
        norm_cust = _normalize_name(cust_name)
        
        user_id = None
        matched_user = r.get('matched_user') or {}
        is_existing = (r.get('user_match_status') == 'existing_user') or matched_user.get('is_existing')
        candidate_uid = r.get('matched_user_id') or matched_user.get('id')

        if is_existing and candidate_uid:
            user_id = candidate_uid
        elif auto_create_renters:
            # Check if created in this batch
            if norm_cust in new_users_batch:
                user_id = new_users_batch[norm_cust]
            else:
                # Create customer profile in users table
                cur.execute("""
                    INSERT INTO users (full_name, phone, email, role, is_verified, created_at)
                    VALUES (%s, %s, %s, 'customer', 2, NOW())
                    RETURNING id
                """, (cust_name, r.get('customer_phone') or None, r.get('customer_email') or None))
                row = cur.fetchone()
                if row:
                    user_id = row['id']
                    new_users_batch[norm_cust] = user_id
                    created_renters_count += 1

        start_date = r['start_date']
        end_date = r['end_date']
        end_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()

        status = 'completed' if end_dt < today else 'confirmed'
        total_price = float(r.get('total_price') or 0.0)
        amount_paid = float(r.get('amount_paid') or 0.0)
        balance = max(0.0, total_price - amount_paid)
        payment_status = 'Paid' if (balance == 0 and total_price > 0) else ('Partially Paid' if amount_paid > 0 else 'Unpaid')

        # Calendar color consistent hash
        color_key = cust_name.lower().strip()
        hash_val = sum(ord(c) for c in color_key) % 12
        palette = ['#fde047', '#86efac', '#93c5fd', '#fdba74', '#d8b4fe', '#fca5a5', '#f472b6', '#5eead4', '#fde68a', '#c7d2fe', '#bef264', '#67e8f9']
        calendar_color = palette[hash_val]

        cur.execute("""
            INSERT INTO bookings (
                vehicle_id, user_id, customer_name, customer_phone, customer_email,
                start_date, end_date, start_time, end_time,
                total_price, base_price, amount_paid, balance_amount,
                status, payment_status, payment_method, service_type, rental_type,
                calendar_color, pickup_location, destination, created_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, '09:00', '17:00',
                %s, %s, %s, %s,
                %s, %s, 'Cash', 'self-drive', 'daily',
                %s, 'Office / Garage', 'Local Tour', NOW()
            ) RETURNING id
        """, (
            vehicle_id, user_id, cust_name, r.get('customer_phone') or 'N/A', r.get('customer_email') or '',
            start_date, end_date,
            total_price, total_price, amount_paid, balance,
            status, payment_status,
            calendar_color
        ))
        b_row = cur.fetchone()
        if b_row:
            imported_bookings_count += 1

    commit_fn()

    return {
        'imported_bookings': imported_bookings_count,
        'created_renters': created_renters_count
    }


def create_sample_excel_template():
    """
    Generates a clean, well-formatted sample Excel template (.xlsx)
    that users can download and populate.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Fleet Bookings Template"

    headers = [
        "Vehicle (Brand/Model - Plate)",
        "Customer Name",
        "Contact Phone",
        "Email (Optional)",
        "Start Date (YYYY-MM-DD)",
        "End Date (YYYY-MM-DD)",
        "Total Rate (PHP)",
        "Amount Paid (PHP)",
        "Payment Status (Paid/Unpaid)"
    ]

    header_fill = PatternFill(start_color="00B14F", end_color="00B14F", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    align_center = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center

    sample_rows = [
        ["VIOS - DAT 1396", "PHILIP FACUNLA", "09171234567", "philip@example.com", "2026-10-12", "2026-10-15", 6000, 6000, "Paid"],
        ["VIOS - NCX 4117", "MARGIE SUAREZ", "09289876543", "", "2026-10-18", "2026-10-22", 8495, 2000, "Partially Paid"],
        ["HONDA BRV - NID 2724", "CASEY ANDREA JALAC", "09995551234", "", "2026-11-01", "2026-11-05", 10400, 10400, "Paid"],
        ["TOYOTA INNOVA - CCK 1126", "JOHN CARLO ORTEGA", "09187778899", "jcarlo@example.com", "2026-11-10", "2026-11-14", 11996, 0, "Unpaid"]
    ]

    for row_data in sample_rows:
        ws.append(row_data)

    # Set column widths
    col_widths = [30, 26, 18, 24, 24, 24, 18, 18, 26]
    for i, width in enumerate(col_widths, 1):
        col_letter = openpyxl.utils.get_column_letter(i)
        ws.column_dimensions[col_letter].width = width

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
