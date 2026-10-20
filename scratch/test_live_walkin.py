import sys
import os
import requests
import json

sys.path.insert(0, os.path.abspath('backend'))
from app import app, get_cursor, commit_db

with app.app_context():
    cur = get_cursor()

    # 1. Fetch an admin user id
    cur.execute("SELECT id, email, role FROM users WHERE LOWER(role) IN ('admin', 'super_admin') LIMIT 1")
    admin = cur.fetchone()
    print(f"Testing with Admin ID: {admin['id']} ({admin['email']})")

    # 2. Fetch an operational vehicle
    cur.execute("SELECT id, brand, model, plate_number, daily_rate FROM vehicles WHERE status = 'Available' LIMIT 1")
    veh = cur.fetchone()
    print(f"Using vehicle: {veh['id']} - {veh['brand']} {veh['model']} ({veh['plate_number']})")

    # 3. Test walk-in API call directly to Vercel production
    payload = {
        "vehicle_id": veh['id'],
        "start_date": "2026-12-25",
        "end_date": "2026-12-26",
        "start_time": "20:40",
        "end_time": "20:40",
        "is_existing_account": False,
        "customer_name": "Test Live Walkin Customer",
        "customer_phone": "09999999999",
        "customer_address": "Test Live Address",
        "emergency_name": "Test Emergency",
        "emergency_phone": "09888888888",
        "emergency_rel": "Sibling",
        "base_price": float(veh['daily_rate'] or 1500),
        "driver_fee": 0,
        "delivery_fee": 0,
        "discount_amount": 0,
        "total_price": float(veh['daily_rate'] or 1500),
        "amount_paid": float(veh['daily_rate'] or 1500),
        "balance_amount": 0,
        "payment_method": "Cash",
        "payment_status": "Paid",
        "status": "Confirmed",
        "rental_type": "Self Drive",
        "pickup_location": "Main Garage Counter",
        "admin_id": admin['id']
    }

    headers = {
        "Content-Type": "application/json",
        "X-Admin-Id": str(admin['id'])
    }

    print("\nSending POST request to https://autoride-booking-system.vercel.app/api/admin/bookings/walkin...")
    r = requests.post("https://autoride-booking-system.vercel.app/api/admin/bookings/walkin", json=payload, headers=headers)
    print(f"Live API Response Status: {r.status_code}")
    print(f"Live API Response Body: {r.text}")

    if r.status_code == 201:
        res_data = r.json()
        new_bk_id = res_data['booking_id']
        print(f"\n[SUCCESS] Live Walk-in Booking created on production with ID {new_bk_id}!")
        
        # Verify in DB:
        cur.execute("SELECT id, user_id, customer_name, customer_phone, total_price, amount_paid, payment_status, status FROM bookings WHERE id = %s", (new_bk_id,))
        bk_row = cur.fetchone()
        print("DB Verification:", dict(bk_row))
        assert bk_row['user_id'] is None, "Pure walk-in MUST have user_id = NULL!"
        print("  -> Confirmed: user_id is NULL (NO user account created)")

        cur.execute("SELECT * FROM payments WHERE booking_id = %s", (new_bk_id,))
        pay_row = cur.fetchone()
        print("Payment Verification:", dict(pay_row) if pay_row else "None")
        assert pay_row is not None, "Counter payment must be recorded!"
        print("  -> Confirmed: Counter payment recorded successfully in payments table")

        # Clean up test row so database stays pristine
        cur.execute("DELETE FROM payments WHERE booking_id = %s", (new_bk_id,))
        cur.execute("DELETE FROM bookings WHERE id = %s", (new_bk_id,))
        commit_db()
        print("\n[CLEANUP] Test booking and payment safely deleted. Database is pristine!")
    else:
        print(f"[FAIL] Unexpected status code: {r.status_code}")
