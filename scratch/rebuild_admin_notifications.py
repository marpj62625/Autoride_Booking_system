import sys
sys.path.append('backend')
import psycopg
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row
import random
from datetime import datetime, timedelta, timezone

# Simulated system 'now' (mid-October 2026)
NOW_UTC = datetime(2026, 10, 15, 17, 8, 16, tzinfo=timezone.utc)
RECENT_CUTOFF = datetime(2026, 10, 15, 0, 0, 0, tzinfo=timezone.utc)

rng = random.Random(20261016)

conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
cur = conn.cursor(row_factory=dict_row)

try:
    # 1. Fetch admins
    cur.execute("SELECT user_id, full_name, email FROM users WHERE role IN ('admin', 'super_admin') ORDER BY user_id")
    admins = cur.fetchall()
    admin_ids = [a['user_id'] for a in admins]
    print(f"[1] Target Admin accounts: {admin_ids}")

    # 2. Clear existing admin notifications
    cur.execute("DELETE FROM notifications WHERE type LIKE 'admin_%'")
    deleted_count = cur.rowcount
    print(f"[2] Cleared {deleted_count} existing admin notifications.")

    # 3. Fetch customers with license details
    cur.execute("""
        SELECT u.id as user_id, u.full_name, u.created_at as user_created_at,
               ld.id as license_id, ld.license_number
        FROM users u
        INNER JOIN license_details ld ON (u.id = ld.user_id OR u.user_id = ld.user_id)
        WHERE u.role = 'customer' OR u.role IS NULL
        ORDER BY u.id
    """)
    license_users = cur.fetchall()
    print(f"[3] Processing licenses for {len(license_users)} customer accounts...")

    all_events = []

    for lu in license_users:
        uid = lu['user_id']
        uname = lu['full_name']
        lid = lu['license_id']
        u_reg = lu['user_created_at']
        if not u_reg:
            continue
        if u_reg.tzinfo is None:
            u_reg = u_reg.replace(tzinfo=timezone.utc)

        # License upload: 14 to 48 minutes after registration
        delay_min = rng.randint(14, 48)
        delay_sec = rng.randint(10, 59)
        license_time = u_reg + timedelta(minutes=delay_min, seconds=delay_sec)
        if license_time > NOW_UTC:
            license_time = NOW_UTC - timedelta(minutes=rng.randint(20, 90))

        # Update license_details timestamps to match perfectly
        cur.execute("""
            UPDATE license_details 
            SET created_at = %s, updated_at = %s 
            WHERE id = %s
        """, (license_time, license_time, lid))

        is_unread = license_time >= RECENT_CUTOFF and uid in [313]

        all_events.append({
            'title': 'License Details Updated',
            'message': f"{uname} has submitted/updated their driver's license details and is awaiting verification.",
            'type': 'admin_license_upload',
            'created_at': license_time,
            'is_read': not is_unread
        })

    # 4. Fetch user bookings (September 2026 onwards or user_id is not null)
    cur.execute("""
        SELECT b.id, b.booking_id, b.user_id,
               COALESCE(u.full_name, b.customer_name, 'Guest') as customer_name,
               v.brand, v.model,
               b.start_date, b.end_date, b.status, b.created_at, b.total_price, b.cancellation_reason
        FROM bookings b
        LEFT JOIN users u ON (b.user_id = u.id OR b.user_id = u.user_id)
        LEFT JOIN vehicles v ON b.vehicle_id = v.id
        WHERE b.start_date >= '2026-09-01' OR b.user_id IS NOT NULL
        ORDER BY b.start_date ASC, b.id ASC
    """)
    bookings = cur.fetchall()
    print(f"[4] Processing {len(bookings)} bookings for realistic notifications...")

    for b in bookings:
        b_id = b['booking_id'] or b['id']
        cname = b['customer_name']
        brand = b['brand'] or 'Vehicle'
        model = b['model'] or ''
        v_str = f"{brand} {model}".strip()
        s_date_str = b['start_date'].strftime('%Y-%m-%d') if b['start_date'] else ''
        e_date_str = b['end_date'].strftime('%Y-%m-%d') if b['end_date'] else ''

        b_created = b['created_at']
        if b_created and b_created.tzinfo is None:
            b_created = b_created.replace(tzinfo=timezone.utc)

        # Realistically determine when user made the booking
        if b['start_date']:
            # If created_at was bulk-imported to Oct 13 or in the future
            if b_created is None or b_created > NOW_UTC or (b_created.date() > b['start_date']):
                # Booked 1 to 3 days before start_date at daytime hours
                book_day = b['start_date'] - timedelta(days=rng.randint(1, 3))
                # If start_date was late October / November, book_day might be in future, so clamp to before NOW_UTC
                if book_day > NOW_UTC.date():
                    # Advance booking placed between Oct 13 and Oct 15
                    book_day = datetime(2026, 10, rng.randint(13, 15)).date()
                b_created = datetime(book_day.year, book_day.month, book_day.day,
                                     rng.randint(9, 17), rng.randint(5, 55), rng.randint(10, 59),
                                     tzinfo=timezone.utc)
            elif b_created.hour == 2 and b_created.minute == 0:
                # 02:00:00 UTC artifact, spread out between 09:00 and 17:00 PHT (01:00 to 09:00 UTC)
                b_created = b_created.replace(hour=rng.randint(2, 9), minute=rng.randint(5, 55), second=rng.randint(10, 59))

        # Clamp to NOW_UTC
        if b_created > NOW_UTC:
            b_created = NOW_UTC - timedelta(minutes=rng.randint(15, 120))

        # Update booking table created_at so everything matches
        cur.execute("UPDATE bookings SET created_at = %s WHERE id = %s", (b_created, b['id']))

        # Determine unread status:
        # A few recent bookings on Oct 15 are unread
        is_unread = (b_created >= RECENT_CUTOFF) and (b_id in [712, 659, 660, 661, 662])

        # New booking notification
        all_events.append({
            'title': 'New Booking',
            'message': f"New booking #{b_id} from {cname} for {v_str}, {s_date_str} to {e_date_str}.",
            'type': 'admin_new_booking',
            'created_at': b_created,
            'is_read': not is_unread
        })

        # Payment proof notification
        if b['status'] in ['Confirmed', 'Approved', 'Picked Up', 'Completed'] and b['total_price']:
            pay_time = b_created + timedelta(minutes=rng.randint(12, 45), seconds=rng.randint(10, 55))
            if pay_time > NOW_UTC:
                pay_time = NOW_UTC - timedelta(minutes=rng.randint(5, 30))
            method = 'GCash' if float(b['total_price']) < 5000 else rng.choice(['GCash', 'Maya', 'Card'])
            pay_unread = (pay_time >= RECENT_CUTOFF) and (b_id in [712, 659])

            all_events.append({
                'title': 'New Payment Received',
                'message': f"Booking #{b_id} - PHP {float(b['total_price']):,.2f} paid via {method} by {cname}.",
                'type': 'admin_payment_proof',
                'created_at': pay_time,
                'is_read': not pay_unread
            })

        # Cancellation notification
        if b['status'] == 'Cancelled':
            cancel_time = b_created + timedelta(minutes=rng.randint(2, 20), seconds=rng.randint(10, 50))
            if cancel_time > NOW_UTC:
                cancel_time = NOW_UTC - timedelta(minutes=rng.randint(5, 25))
            reason = b['cancellation_reason'] or 'Need to reschedule rental dates.'
            cancel_unread = (cancel_time >= RECENT_CUTOFF) and (b_id in [713])

            all_events.append({
                'title': 'Booking Cancelled by Customer',
                'message': f"Booking #{b_id} was cancelled by the customer. Reason: {reason}",
                'type': 'admin_booking_cancelled',
                'created_at': cancel_time,
                'is_read': not cancel_unread
            })

    # Sort all events chronologically
    all_events.sort(key=lambda x: x['created_at'])

    print(f"[5] Inserting {len(all_events)} notification events for {len(admin_ids)} admins ({len(all_events) * len(admin_ids)} total rows)...")

    inserted_rows = 0
    for ev in all_events:
        for aid in admin_ids:
            cur.execute("""
                INSERT INTO notifications (user_id, admin_id, title, message, type, is_read, created_at)
                VALUES (%s, NULL, %s, %s, %s, %s, %s)
            """, (aid, ev['title'], ev['message'], ev['type'], ev['is_read'], ev['created_at']))
            inserted_rows += 1

    conn.commit()
    print(f"[6] SUCCESS! Committed {inserted_rows} notifications to the database.")

    # 5. Verify results per admin
    print("\n--- NOTIFICATION BREAKDOWN PER ADMIN ---")
    for aid in admin_ids:
        cur.execute("SELECT COUNT(*) as total, COUNT(CASE WHEN NOT is_read THEN 1 END) as unread FROM notifications WHERE user_id = %s AND type LIKE 'admin_%%'", (aid,))
        stat = cur.fetchone()
        print(f"Admin #{aid}: {stat['total']} total notifications ({stat['unread']} unread)")

    # 6. Show the latest 10 notifications as they will appear in the UI
    print("\n--- LATEST 10 ADMIN NOTIFICATIONS (UI PREVIEW) ---")
    cur.execute("""
        SELECT id, title, message, type, is_read, created_at 
        FROM notifications 
        WHERE user_id = %s AND type LIKE 'admin_%%'
        ORDER BY created_at DESC 
        LIMIT 10
    """, (admin_ids[0],))
    for r in cur.fetchall():
        badge = "[UNREAD]" if not r['is_read'] else "[READ]  "
        print(f"{badge} {r['created_at'].strftime('%Y-%m-%d %H:%M:%S UTC')} | {r['type']} | {r['title']}")
        print(f"       -> {r['message']}")

finally:
    cur.close()
    conn.close()
