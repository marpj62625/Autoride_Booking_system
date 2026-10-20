import sys
sys.path.insert(0, 'backend')
import psycopg2
from config import SUPABASE_DB_URL
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(SUPABASE_DB_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

user_ids = [25, 26, 27, 28, 29, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]

print("=== 1. USERS & LICENSE DETAILS (16 USERS) ===")
cur.execute("""
    SELECT u.id, u.full_name, u.email, u.phone,
           u.barangay, u.municipality, u.province,
           ld.address as license_address,
           ld.issuing_country_state,
           ld.license_number
    FROM users u
    LEFT JOIN license_details ld ON u.id = ld.user_id
    WHERE u.id = ANY(%s)
    ORDER BY u.id ASC;
""", (user_ids,))
users = cur.fetchall()
user_map = {}
for u in users:
    user_map[u['id']] = u
    u_addr = ', '.join(filter(None, [u['barangay'], u['municipality'], u['province']]))
    print(f"User #{u['id']}: {u['full_name']}")
    print(f"   Users table addr   : '{u_addr}'")
    print(f"   License addr       : '{u['license_address']}'")
    print(f"   License number     : '{u['license_number']}'")

print("\n=== 2. BOOKINGS OF 16 USERS ===")
cur.execute("""
    SELECT b.id, b.user_id, b.customer_name, b.customer_address,
           b.start_date, b.end_date, b.status,
           b.pickup_location, b.destination
    FROM bookings b
    WHERE b.user_id = ANY(%s)
    ORDER BY b.id ASC;
""", (user_ids,))
bookings = cur.fetchall()
print(f"Total bookings: {len(bookings)}")

empty_bookings = []
mismatched_bookings = []

for b in bookings:
    u = user_map.get(b['user_id'], {})
    u_name = u.get('full_name') or b['customer_name']
    lic_addr = (u.get('license_address') or u.get('issuing_country_state') or '').strip()
    b_addr = (b['customer_address'] or '').strip()
    
    if not b_addr:
        empty_bookings.append({
            'booking_id': b['id'],
            'user_id': b['user_id'],
            'user_name': u_name,
            'dates': f"{b['start_date']} to {b['end_date']}",
            'booking_address': '[EMPTY / NONE]',
            'license_address': lic_addr,
            'pickup': b['pickup_location'],
            'destination': b['destination']
        })
    elif b_addr != lic_addr:
        mismatched_bookings.append({
            'booking_id': b['id'],
            'user_id': b['user_id'],
            'user_name': u_name,
            'dates': f"{b['start_date']} to {b['end_date']}",
            'booking_address': b_addr,
            'license_address': lic_addr,
            'pickup': b['pickup_location'],
            'destination': b['destination']
        })

print(f"\n--- A. BOOKINGS WITH EMPTY ADDRESS ({len(empty_bookings)}): ---")
for x in empty_bookings:
    print(f"Booking #{x['booking_id']} | User #{x['user_id']} ({x['user_name']}) | Dates: {x['dates']}")
    print(f"   Booking Address: {x['booking_address']}")
    print(f"   License Address: {x['license_address']}")

print(f"\n--- B. BOOKINGS WITH DIFFERENT ADDRESS ({len(mismatched_bookings)}): ---")
for x in mismatched_bookings:
    print(f"Booking #{x['booking_id']} | User #{x['user_id']} ({x['user_name']}) | Dates: {x['dates']}")
    print(f"   Booking Address: '{x['booking_address']}'")
    print(f"   License Address: '{x['license_address']}'")

conn.close()
