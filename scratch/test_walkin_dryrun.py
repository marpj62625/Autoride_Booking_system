import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
from app import app, get_cursor, get_db

with app.app_context():
    conn = get_db()
    with conn.transaction():
        cur = get_cursor()
        # Find an available vehicle
        cur.execute("SELECT id, brand, model, plate_number, daily_rate FROM vehicles WHERE status NOT IN ('Maintenance', 'Repair') LIMIT 1")
        veh = cur.fetchone()
        print("Selected test vehicle:", veh)

        cur.execute("""
            INSERT INTO bookings (
                user_id, vehicle_id, start_date, end_date, start_time, end_time,
                pickup_location, rental_type, service_type,
                customer_name, customer_phone, customer_address,
                base_price, total_price, amount_paid, balance_amount,
                status, payment_status, payment_type, payment_method,
                destination, rental_purpose, created_at
            ) VALUES (
                NULL, %s, CURRENT_DATE, CURRENT_DATE + INTERVAL '2 days', '20:40', '20:40',
                'Main Office', 'Self Drive', 'pickup',
                'Juan Dela Cruz (Walk-in)', '09171234567', 'Brgy Central, Metro Manila',
                3000.00, 3000.00, 3000.00, 0.00,
                'Picked Up', 'Paid', 'Full', 'Cash',
                'Tagaytay Tour', 'Walk-in Counter Rental', NOW()
            ) RETURNING id, booking_id
        """, (veh['id'],))
        row = cur.fetchone()
        test_b_id = row['id']
        print(f"Created test walk-in booking #{test_b_id}")

        # Test querying it via admin bookings query
        cur.execute("""
            SELECT b.id, b.user_id, COALESCE(u.full_name, b.customer_name, 'Customer') AS customer_name,
                   COALESCE(u.phone, b.customer_phone, '') AS customer_phone,
                   CONCAT(v.brand, ' ', v.model, ' (', v.plate_number, ')') AS car,
                   b.status, b.payment_status, b.total_price
            FROM bookings b
            LEFT JOIN users u ON b.user_id = u.id
            LEFT JOIN vehicles v ON b.vehicle_id = v.id
            WHERE b.id = %s
        """, (test_b_id,))
        admin_bk = cur.fetchone()
        print("Admin query result for walk-in booking:", admin_bk)

        # Test querying it via fleet-calendar query
        cur.execute("""
            SELECT b.id, b.vehicle_id, b.user_id,
                   COALESCE(NULLIF(TRIM(u.full_name), ''), NULLIF(TRIM(b.customer_name), ''), 'Customer') AS customer_name,
                   v.plate_number, b.status
            FROM bookings b
            JOIN vehicles v ON b.vehicle_id = v.id
            LEFT JOIN users u ON b.user_id = u.id
            WHERE b.id = %s
        """, (test_b_id,))
        cal_bk = cur.fetchone()
        print("Fleet calendar query result for walk-in booking:", cal_bk)

        # Roll back transaction so database is left pristine
        conn.rollback()
        print("[TEST PASSED: Walk-in booking with user_id = NULL queries cleanly without errors!]")
