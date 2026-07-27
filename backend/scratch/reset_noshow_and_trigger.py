import psycopg
from psycopg.rows import dict_row

DB_URL = "postgresql://postgres.fydfsgjrlowrrtlmefwq:Autoride777%25*@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
PH_TZ_OFFSET = 8

from datetime import datetime, timezone, timedelta
PH = timezone(timedelta(hours=PH_TZ_OFFSET))
now_ph = datetime.now(tz=PH)

conn = psycopg.connect(conninfo=DB_URL, row_factory=dict_row)
cur = conn.cursor()

# 1. Reset no_show_notified_at for all Confirmed/Approved bookings
cur.execute("""
    UPDATE bookings
    SET no_show_notified_at = NULL
    WHERE status IN ('Confirmed', 'Approved')
      AND no_show_notified_at IS NOT NULL
    RETURNING id, start_date, start_time
""")
reset_rows = cur.fetchall()
conn.commit()
print(f"\n[RESET] Cleared no_show_notified_at for {len(reset_rows)} booking(s):")
for r in reset_rows:
    print(f"  Booking #{r['id']} - {r['start_date']} {r['start_time']}")

# 2. Get overdue bookings joined with user name
cur.execute("""
    SELECT b.id, b.start_date, b.start_time, b.no_show_notified_at,
           COALESCE(u.full_name, 'Unknown') as customer_name
    FROM bookings b
    LEFT JOIN users u ON b.user_id = u.id
    WHERE b.status IN ('Confirmed', 'Approved')
      AND b.no_show_notified_at IS NULL
""")
bookings = cur.fetchall()
print(f"\n[CHECK] Found {len(bookings)} bookings to evaluate...")

notified = 0
for bk in bookings:
    pickup_date = bk['start_date']
    if hasattr(pickup_date, 'date'):
        pickup_date = pickup_date.date()

    pickup_time_raw = bk.get('start_time') or '06:00'
    if hasattr(pickup_time_raw, 'strftime'):
        pickup_time_str = pickup_time_raw.strftime('%H:%M')
    else:
        pickup_time_str = str(pickup_time_raw)[:5]

    try:
        ph_hour, ph_min = map(int, pickup_time_str.split(':'))
    except Exception:
        ph_hour, ph_min = 6, 0

    pickup_dt = datetime(pickup_date.year, pickup_date.month, pickup_date.day, ph_hour, ph_min, tzinfo=PH)
    deadline_dt = pickup_dt + timedelta(hours=2)
    hours_past = (now_ph - pickup_dt).total_seconds() / 3600

    print(f"\n  Booking #{bk['id']} ({bk['customer_name']}) - pickup: {pickup_date} {pickup_time_str} | {hours_past:.1f}h ago")

    if now_ph >= deadline_dt:
        print(f"    -> OVERDUE! Sending no-show alert...")

        # Get admins from users table
        cur2 = conn.cursor(row_factory=dict_row)
        cur2.execute("SELECT id FROM users WHERE role IN ('admin', 'super_admin')")
        admins = list(cur2.fetchall())

        print(f"    -> Admins found: {[a['id'] for a in admins]}")

        for admin in admins:
            try:
                conn.cursor().execute(
                    "INSERT INTO notifications (user_id, admin_id, title, message, type) VALUES (%s, NULL, %s, %s, %s)",
                    (
                        admin['id'],
                        f"\u26a0\ufe0f No Show Alert: Booking #{bk['id']}",
                        f"Customer '{bk['customer_name']}' has not shown up. Scheduled pickup was {pickup_date} at {pickup_time_str} PH. Please mark as No Show.",
                        "admin_no_show"
                    )
                )
                print(f"    -> Notification inserted for admin user_id={admin['id']}")
            except Exception as e:
                print(f"    -> FAILED for admin user_id={admin['id']}: {e}")

        conn.cursor().execute("UPDATE bookings SET no_show_notified_at = NOW() WHERE id = %s", (bk['id'],))
        conn.commit()
        notified += 1
    else:
        print(f"    -> Not yet overdue. Deadline: {deadline_dt.strftime('%Y-%m-%d %H:%M')} PH")

print(f"\n[DONE] Sent no-show alerts for {notified} booking(s).")
conn.close()
