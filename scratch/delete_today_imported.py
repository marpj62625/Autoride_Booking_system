import sys
sys.path.append('backend')
from database import get_connection
from psycopg.rows import dict_row

conn = get_connection()
conn.autocommit = False
cur = conn.cursor(row_factory=dict_row)

try:
    # 1. Fetch exactly the bookings to be deleted to verify
    cur.execute("""
        SELECT id, customer_name, start_date, end_date, created_at
        FROM bookings
        WHERE id >= 664 AND id <= 692
          AND created_at >= '2026-10-13 07:40:00+00'
        ORDER BY id ASC
    """)
    target_bookings = cur.fetchall()
    print(f"Target bookings found: {len(target_bookings)}")

    # 2. Fetch exactly the users to be deleted to verify
    cur.execute("""
        SELECT id, first_name, last_name, full_name, created_at
        FROM users
        WHERE id >= 283 AND id <= 310
          AND created_at >= '2026-10-13 07:40:00+00'
        ORDER BY id ASC
    """)
    target_users = cur.fetchall()
    print(f"Target users found: {len(target_users)}")

    assert len(target_bookings) == 29, f"Expected 29 bookings, found {len(target_bookings)}"
    assert len(target_users) == 28, f"Expected 28 users, found {len(target_users)}"

    # 3. Delete bookings first (foreign key dependency on users)
    cur.execute("""
        DELETE FROM bookings
        WHERE id >= 664 AND id <= 692
          AND created_at >= '2026-10-13 07:40:00+00'
    """)
    deleted_bookings_count = cur.rowcount
    print(f"Deleted bookings rowcount: {deleted_bookings_count}")

    # 4. Delete users
    cur.execute("""
        DELETE FROM users
        WHERE id >= 283 AND id <= 310
          AND created_at >= '2026-10-13 07:40:00+00'
    """)
    deleted_users_count = cur.rowcount
    print(f"Deleted users rowcount: {deleted_users_count}")

    if deleted_bookings_count == 29 and deleted_users_count == 28:
        conn.commit()
        print("SUCCESS: Transaction committed successfully!")
    else:
        conn.rollback()
        print("WARNING: Rowcounts did not match, rolled back!")

except Exception as e:
    conn.rollback()
    print("ERROR occurred, rolled back:", e)
finally:
    conn.close()
