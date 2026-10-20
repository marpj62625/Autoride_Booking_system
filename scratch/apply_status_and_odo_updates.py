import sys, os
sys.path.append(os.path.abspath('backend'))
from database import get_connection
from psycopg.rows import dict_row

conn = get_connection()
conn.autocommit = False
cur = conn.cursor(row_factory=dict_row)

try:
    print("=== 1. UPDATING BOOKING STATUSES ===")

    # Completed bookings
    # #693: ended 2026-10-01
    cur.execute("""
        UPDATE bookings 
        SET status = 'Completed', completed_at = '2026-10-01 17:00:00'
        WHERE id = 693
    """)
    print("Updated #693 -> Completed")

    # #696: ended 2026-10-08
    cur.execute("""
        UPDATE bookings 
        SET status = 'Completed', completed_at = '2026-10-08 17:00:00'
        WHERE id = 696
    """)
    print("Updated #696 -> Completed")

    # #697: ended 2026-10-11
    cur.execute("""
        UPDATE bookings 
        SET status = 'Completed', completed_at = '2026-10-11 17:00:00'
        WHERE id = 697
    """)
    print("Updated #697 -> Completed")

    # Active / Ongoing bookings -> Picked Up
    # #694: 2026-10-01 to 2026-10-30
    cur.execute("""
        UPDATE bookings 
        SET status = 'Picked Up'
        WHERE id = 694
    """)
    print("Updated #694 -> Picked Up")

    # #695: 2026-10-06 to 2026-10-13
    cur.execute("""
        UPDATE bookings 
        SET status = 'Picked Up'
        WHERE id = 695
    """)
    print("Updated #695 -> Picked Up")

    # #698: 2026-10-12 to 2026-10-17
    cur.execute("""
        UPDATE bookings 
        SET status = 'Picked Up'
        WHERE id = 698
    """)
    print("Updated #698 -> Picked Up")

    # #699: 2026-10-12 to 2026-10-19
    cur.execute("""
        UPDATE bookings 
        SET status = 'Picked Up'
        WHERE id = 699
    """)
    print("Updated #699 -> Picked Up")

    print("\n=== 2. UPDATING VEHICLE ODOMETERS ===")
    # Veh 17 (Toyota Vios XE AT - DAT 1396): 100,060 -> 100,405 (+345 km)
    cur.execute("""
        UPDATE vehicles 
        SET odometer = 100405
        WHERE id = 17
        RETURNING id, brand, model, plate_number, odometer
    """)
    v17 = cur.fetchone()
    print(f"Updated Veh #{v17['id']} ({v17['brand']} {v17['model']} - {v17['plate_number']}) Odometer to: {v17['odometer']} km")

    # Veh 26 (Toyota Innova XE AT - NHN 5388): 200,062 -> 200,422 (+360 km)
    cur.execute("""
        UPDATE vehicles 
        SET odometer = 200422
        WHERE id = 26
        RETURNING id, brand, model, plate_number, odometer
    """)
    v26 = cur.fetchone()
    print(f"Updated Veh #{v26['id']} ({v26['brand']} {v26['model']} - {v26['plate_number']}) Odometer to: {v26['odometer']} km")

    conn.commit()
    print("\n>>> All database changes committed successfully! <<<")

except Exception as e:
    conn.rollback()
    print("Error during update, rolled back:", e)
    raise
finally:
    conn.close()
