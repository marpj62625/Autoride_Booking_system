import sys
sys.path.insert(0, 'backend')
import psycopg2
from config import SUPABASE_DB_URL
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(SUPABASE_DB_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

# 1. Check bookings columns
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'bookings'
    ORDER BY ordinal_position;
""")
cols = [r['column_name'] for r in cur.fetchall()]
print("Bookings columns:", cols)

# 2. Check bookings for the 16 users
user_ids = [25, 26, 27, 28, 29, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]

cur.execute("""
    SELECT b.id, b.user_id, b.customer_name, b.customer_phone,
           b.pickup_location, b.destination,
           u.full_name as user_full_name, u.phone as user_phone,
           ld.address as license_address,
           ld.issuing_country_state,
           ld.license_number,
           ld.full_name as license_full_name
    FROM bookings b
    LEFT JOIN users u ON b.user_id = u.id
    LEFT JOIN license_details ld ON b.user_id = ld.user_id
    WHERE b.user_id = ANY(%s)
    ORDER BY b.id ASC;
""", (user_ids,))

rows = cur.fetchall()
print(f"\nTotal bookings for 16 users: {len(rows)}")
for r in rows:
    print(f"Booking #{r['id']} | User #{r['user_id']} ({r['user_full_name']}):")
    print(f"  customer_name: {r['customer_name']}")
    print(f"  license_full_name: {r['license_full_name']}")
    print(f"  license_number: {r['license_number']}")
    print(f"  license_address: {r['license_address']}")
    print(f"  pickup_location: {r['pickup_location']}")
    print(f"  destination: {r['destination']}")
    print("-" * 50)

conn.close()
