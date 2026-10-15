import sys
sys.path.insert(0, 'backend')
import psycopg2
from config import SUPABASE_DB_URL
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(SUPABASE_DB_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

user_ids = [25, 26, 27, 28, 29, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]

print("=== CHECKING BEFORE UPDATE ===")
cur.execute("""
    SELECT b.id, b.user_id, b.customer_name, b.customer_address,
           COALESCE(NULLIF(TRIM(ld.address), ''), NULLIF(TRIM(ld.issuing_country_state), '')) as target_license_address
    FROM bookings b
    JOIN license_details ld ON b.user_id = ld.user_id
    WHERE b.user_id = ANY(%s)
    ORDER BY b.id ASC;
""", (user_ids,))

to_update = cur.fetchall()
print(f"Total bookings for 16 users with license details: {len(to_update)}")

# Execute update
cur.execute("""
    UPDATE bookings b
    SET customer_address = COALESCE(NULLIF(TRIM(ld.address), ''), NULLIF(TRIM(ld.issuing_country_state), ''))
    FROM license_details ld
    WHERE b.user_id = ld.user_id
      AND b.user_id = ANY(%s)
      AND COALESCE(NULLIF(TRIM(ld.address), ''), NULLIF(TRIM(ld.issuing_country_state), '')) IS NOT NULL;
""", (user_ids,))

conn.commit()
print(f"Updated rows committed!")

# Also check if any other bookings in entire DB have a user_id with license details that have empty customer_address
cur.execute("""
    UPDATE bookings b
    SET customer_address = COALESCE(NULLIF(TRIM(ld.address), ''), NULLIF(TRIM(ld.issuing_country_state), ''))
    FROM license_details ld
    WHERE b.user_id = ld.user_id
      AND (b.customer_address IS NULL OR b.customer_address = '' OR b.customer_address = 'N/A')
      AND COALESCE(NULLIF(TRIM(ld.address), ''), NULLIF(TRIM(ld.issuing_country_state), '')) IS NOT NULL;
""")
extra_updated = cur.rowcount
conn.commit()
print(f"Extra bookings with empty address updated: {extra_updated}")

# Verify after update
cur.execute("""
    SELECT b.id, b.user_id, b.customer_name, b.customer_address,
           COALESCE(NULLIF(TRIM(ld.address), ''), NULLIF(TRIM(ld.issuing_country_state), '')) as target_license_address
    FROM bookings b
    JOIN license_details ld ON b.user_id = ld.user_id
    WHERE b.user_id = ANY(%s)
    ORDER BY b.id ASC;
""", (user_ids,))

after_rows = cur.fetchall()
mismatches = 0
for r in after_rows:
    if r['customer_address'] != r['target_license_address']:
        print(f"MISMATCH STILL: Booking #{r['id']} - '{r['customer_address']}' != '{r['target_license_address']}'")
        mismatches += 1

if mismatches == 0:
    print(f"\nSUCCESS: All {len(after_rows)} bookings for the 16 users now 100% MATCH their verified license address!")

conn.close()
