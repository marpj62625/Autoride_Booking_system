import os, sys
sys.path.insert(0, '.')
from database import get_connection

conn = get_connection()
cur = conn.cursor()

VERIFIED_IDS = [25, 26, 27, 28, 29, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]

print("=== 1. VERIFIED 16 USERS BREAKDOWN ===")
cur.execute("""
    SELECT u.id, u.full_name, u.email, u.loyalty_points, u.is_regular_customer,
           COUNT(b.id) AS total_bookings,
           COUNT(b.id) FILTER (WHERE b.status = 'Completed') AS completed_bookings,
           COALESCE(SUM(b.total_price), 0) AS total_spent
    FROM users u
    LEFT JOIN bookings b ON u.id = b.user_id
    WHERE u.id = ANY(%s)
    GROUP BY u.id, u.full_name, u.email, u.loyalty_points, u.is_regular_customer
    ORDER BY u.id
""", (VERIFIED_IDS,))

for r in cur.fetchall():
    vip = "[VIP REGULAR]" if r[4] else ""
    print(f"UID {r[0]:02d}: {r[1]} | Email: {r[2]} | Pts: {r[3]} | Spent: PHP {r[7]:,.2f} | Bookings: {r[5]} (Completed: {r[6]}) {vip}")

print("\n=== 2. ARVIN CORPUZ BOOKINGS (User ID 25) ===")
cur.execute("""
    SELECT id, vehicle_id, start_date, end_date, total_price, status, customer_name 
    FROM bookings 
    WHERE user_id = 25 
    ORDER BY start_date
""")
for b in cur.fetchall():
    print(f"  Booking #{b[0]}: {b[2]} to {b[3]} | Veh ID {b[1]} | PHP {b[4]:,.2f} | Status: {b[5]} | Cust: {b[6]}")

print("\n=== 3. HUBERT SANCHEZ BOOKINGS (User ID 28) ===")
cur.execute("""
    SELECT id, vehicle_id, start_date, end_date, total_price, status, customer_name 
    FROM bookings 
    WHERE user_id = 28 
    ORDER BY start_date
""")
for b in cur.fetchall():
    print(f"  Booking #{b[0]}: {b[2]} to {b[3]} | Veh ID {b[1]} | PHP {b[4]:,.2f} | Status: {b[5]} | Cust: {b[6]}")

print("\n=== 4. BOOKING #341 (User ID 52 testcompany lal) ===")
cur.execute("""
    SELECT b.id, b.user_id, u.full_name, u.email, b.vehicle_id, b.start_date, b.end_date, b.total_price, b.status
    FROM bookings b
    JOIN users u ON b.user_id = u.id
    WHERE b.id = 341
""")
print("  Booking 341:", cur.fetchone())

print("\n=== 5. NON-VERIFIED CUSTOMERS SAMPLE (NO EMAIL) ===")
cur.execute("""
    SELECT u.id, u.full_name, u.email, u.is_verified, COUNT(b.id) AS bookings_count, COALESCE(SUM(b.total_price), 0) AS total_spent
    FROM users u
    JOIN bookings b ON u.id = b.user_id
    WHERE u.email IS NULL
    GROUP BY u.id, u.full_name, u.email, u.is_verified
    ORDER BY bookings_count DESC
    LIMIT 10
""")
for r in cur.fetchall():
    print(f"  UID {r[0]}: {r[1]} | Email: {r[2]} | Verified: {r[3]} | Bookings: {r[4]} | Spent: PHP {r[5]:,.2f}")

print("\n=== 6. TOTAL BOOKINGS & USERS SUMMARY ===")
cur.execute("SELECT COUNT(*) FROM bookings")
print(f"Total bookings in DB: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM bookings WHERE user_id = ANY(%s)", (VERIFIED_IDS,))
print(f"Bookings belonging to 16 verified users: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM bookings WHERE user_id != ALL(%s) AND id != 341", (VERIFIED_IDS,))
print(f"Bookings belonging to other past customers (no email): {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM users WHERE email IS NULL")
print(f"Total unverified past customer accounts (no email): {cur.fetchone()[0]}")

conn.close()
