import sys
sys.path.append('backend')
import psycopg
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row
import random
from datetime import datetime, timedelta, timezone

# Connect
conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)

# 1. Fetch admins
cur.execute("SELECT user_id, full_name, email FROM users WHERE role IN ('admin', 'super_admin') ORDER BY user_id")
admins = cur.fetchall()
admin_ids = [a['user_id'] for a in admins]
print(f"Target Admins: {admin_ids}")

# 2. Fetch customers and their license details
cur.execute("""
    SELECT u.id as user_id, u.full_name, u.created_at as user_created_at,
           ld.id as license_id, ld.license_number, ld.created_at as current_license_created_at
    FROM users u
    LEFT JOIN license_details ld ON (u.id = ld.user_id OR u.user_id = ld.user_id)
    WHERE u.role = 'customer' OR u.role IS NULL
    ORDER BY u.id
""")
users = cur.fetchall()
print(f"Total customers: {len(users)}")

# 3. Fetch all bookings
cur.execute("""
    SELECT b.id, b.booking_id, b.user_id,
           COALESCE(u.full_name, b.customer_name, 'Guest') as customer_name,
           v.brand, v.model,
           b.start_date, b.end_date, b.status, b.created_at, b.total_price, b.cancellation_reason
    FROM bookings b
    LEFT JOIN users u ON (b.user_id = u.id OR b.user_id = u.user_id)
    LEFT JOIN vehicles v ON b.vehicle_id = v.id
    ORDER BY b.id ASC
""")
bookings = cur.fetchall()
print(f"Total bookings: {len(bookings)}")

cur.close()
conn.close()

# Prepare notifications list
events = []

# --- A. LICENSE UPLOAD NOTIFICATIONS ---
# Deterministic seed so it's consistent if re-run, but realistic & varied per user
rng = random.Random(42)

for u in users:
    if not u['license_id']:
        continue
    uname = u['full_name'] or 'Customer'
    u_created = u['user_created_at']
    if not u_created:
        continue
    if u_created.tzinfo is None:
        u_created = u_created.replace(tzinfo=timezone.utc)
        
    # Random realistic upload delay: 14 to 48 minutes after registration
    delay_minutes = rng.randint(14, 48)
    delay_seconds = rng.randint(10, 59)
    license_upload_time = u_created + timedelta(minutes=delay_minutes, seconds=delay_seconds)
    
    # Is read?
    # Anything before Oct 15 is read, Oct 15 onwards might be unread
    is_read = license_upload_time < datetime(2026, 10, 15, 0, 0, 0, tzinfo=timezone.utc)
    if u['user_id'] in [313, 314]: # Brand new registrations
        is_read = rng.choice([False, True])

    events.append({
        'type': 'admin_license_upload',
        'title': 'License Details Updated',
        'message': f"{uname} has submitted/updated their driver's license details and is awaiting verification.",
        'created_at': license_upload_time,
        'is_read': is_read,
        'user_id_ref': u['user_id'],
        'license_id': u['license_id']
    })

# --- B. BOOKING NOTIFICATIONS ---
for b in bookings:
    b_id = b['booking_id'] or b['id']
    cname = b['customer_name']
    brand = b['brand'] or 'Vehicle'
    model = b['model'] or ''
    vehicle_str = f"{brand} {model}".strip()
    s_date = b['start_date'].strftime('%Y-%m-%d') if b['start_date'] else 'TBD'
    e_date = b['end_date'].strftime('%Y-%m-%d') if b['end_date'] else 'TBD'
    
    # Booking creation timestamp:
    b_created = b['created_at']
    if b_created and b_created.tzinfo is None:
        b_created = b_created.replace(tzinfo=timezone.utc)
        
    # For bookings where b_created was bulk-set to 2026-10-13 08:24:48, but start_date was earlier (e.g. Oct 1, Oct 6, Oct 10):
    # Adjust booking created_at to 1-3 days before start_date so it's 100% realistic
    if b['start_date'] and b_created and b['start_date'] < b_created.date():
        # Set to 2 days prior at a realistic daytime hour
        book_day = b['start_date'] - timedelta(days=rng.randint(1, 3))
        b_created = datetime(book_day.year, book_day.month, book_day.day, 
                             rng.randint(9, 17), rng.randint(5, 55), rng.randint(10, 59), 
                             tzinfo=timezone.utc)
    elif b['created_at'] and b['created_at'].hour == 2 and b['created_at'].minute == 0:
        # Some imported ones had exact 02:00:00 UTC (10:00 AM PHT), add natural variation in minutes/seconds
        b_created = b['created_at'].replace(hour=rng.randint(9, 16), minute=rng.randint(5, 55), second=rng.randint(10, 59))
        
    # Unread status: Bookings from Oct 14 onwards can have unread notifications
    is_read = b_created < datetime(2026, 10, 14, 0, 0, 0, tzinfo=timezone.utc)
    if b_created >= datetime(2026, 10, 15, 0, 0, 0, tzinfo=timezone.utc):
        # Recent bookings
        is_read = False if b_id in [712, 659, 660, 661, 662] else True

    # 1. New Booking notification
    events.append({
        'type': 'admin_new_booking',
        'title': 'New Booking',
        'message': f"New booking #{b_id} from {cname} for {vehicle_str}, {s_date} to {e_date}.",
        'created_at': b_created,
        'is_read': is_read,
        'booking_id': b_id,
        'booking_db_id': b['id']
    })

    # 2. Payment proof / Payment received for confirmed/paid bookings
    if b['status'] in ['Confirmed', 'Approved', 'Picked Up', 'Completed'] and b['total_price']:
        pay_time = b_created + timedelta(minutes=rng.randint(10, 45), seconds=rng.randint(10, 55))
        pay_read = pay_time < datetime(2026, 10, 15, 0, 0, 0, tzinfo=timezone.utc)
        method = 'GCash' if float(b['total_price']) < 5000 else rng.choice(['GCash', 'Maya', 'Card'])
        events.append({
            'type': 'admin_payment_proof',
            'title': 'New Payment Received',
            'message': f"Booking #{b_id} - PHP {float(b['total_price']):,.2f} paid via {method} by {cname}.",
            'created_at': pay_time,
            'is_read': pay_read,
            'booking_id': b_id
        })

    # 3. Cancellation if cancelled
    if b['status'] == 'Cancelled':
        cancel_time = b_created + timedelta(minutes=rng.randint(2, 25), seconds=rng.randint(10, 50))
        reason = b['cancellation_reason'] or 'Need to reschedule rental dates.'
        events.append({
            'type': 'admin_booking_cancelled',
            'title': 'Booking Cancelled by Customer',
            'message': f"Booking #{b_id} was cancelled by the customer. Reason: {reason}",
            'created_at': cancel_time,
            'is_read': False if cancel_time >= datetime(2026, 10, 15, 0, 0, 0, tzinfo=timezone.utc) else True,
            'booking_id': b_id
        })

# Sort all events chronologically
events.sort(key=lambda x: x['created_at'])

print(f"\nTotal realistic notification events generated: {len(events)}")
print(f"Total rows to insert (x {len(admin_ids)} admins): {len(events) * len(admin_ids)}")

print("\n--- SAMPLE GENERATED FEED (LATEST 15 NOTIFICATIONS) ---")
for ev in events[-15:]:
    status_label = "[UNREAD]" if not ev['is_read'] else "[READ]  "
    ts_str = ev['created_at'].strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f"{status_label} {ts_str} | {ev['type']} | {ev['title']} | {ev['message']}")
