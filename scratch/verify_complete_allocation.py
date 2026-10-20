import sys, os, datetime
sys.path.append(os.path.abspath('backend'))
from database import get_connection
from psycopg.rows import dict_row

conn = get_connection()
cur = conn.cursor(row_factory=dict_row)

user_ids = [25, 26, 27, 28, 29, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]

print("=== FINAL CONFLICT-CHECK AUDIT FOR ALL 16 USERS ===")
violations = []

for uid in user_ids:
    cur.execute("""
        SELECT b.id, b.user_id, u.full_name, b.vehicle_id, v.brand, v.model, v.plate_number,
               b.start_date, b.end_date, b.status
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN vehicles v ON b.vehicle_id = v.id
        WHERE b.user_id = %s AND b.start_date >= '2026-09-01'
        ORDER BY b.start_date ASC
    """, (uid,))
    bks = cur.fetchall()

    print(f"\nUser #{uid}: {bks[0]['full_name'] if bks else 'N/A'} (Total bookings: {len(bks)})")
    for i, b in enumerate(bks):
        print(f"  [{i+1}] Booking #{b['id']} | {b['start_date']} -> {b['end_date']} | {b['brand']} {b['model']} ({b['plate_number']})")
        # Check against every other booking of this user
        for j, other in enumerate(bks):
            if i >= j: continue
            # Overlap check
            if b['start_date'] <= other['end_date'] and b['end_date'] >= other['start_date']:
                violations.append(f"OVERLAP: User #{uid} Bookings #{b['id']} and #{other['id']}")
            # Immediate consecutive day on different car check
            gap = (other['start_date'] - b['end_date']).days
            if gap in (0, 1) and b['vehicle_id'] != other['vehicle_id']:
                violations.append(f"CONSECUTIVE CAR-HOP: User #{uid} Bookings #{b['id']} and #{other['id']} (gap: {gap} days on different cars)")

print("\n" + "="*50)
if violations:
    print(f"FAILED: Found {len(violations)} violations:")
    for v in violations:
        print("  -", v)
else:
    print("PASSED: 100% ZERO CONFLICTS DETECTED ACROSS ALL 16 USERS!")
print("="*50)

conn.close()
