import sys
import os
import json
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.abspath('backend'))
from app import app, get_cursor, commit_db

with app.app_context():
    client = app.test_client()

    # Find a valid vehicle for testing
    cur = get_cursor()
    cur.execute("SELECT id, brand, model, plate_number, daily_rate FROM vehicles WHERE status NOT IN ('Maintenance', 'Repair') LIMIT 1")
    veh = cur.fetchone()
    assert veh, "Must have at least 1 vehicle"
    v_id = veh['id']
    print(f"Using vehicle #{v_id} ({veh['brand']} {veh['model']}) for tests.")

    # Find an admin token or simulate admin session
    # We can fetch an admin user
    cur.execute("SELECT id, email, role FROM users WHERE role IN ('admin', 'super_admin') LIMIT 1")
    admin_user = cur.fetchone()
    admin_id = admin_user['id'] if admin_user else 1

    headers = {'X-Admin-Id': str(admin_id)}

    cur.execute("DELETE FROM payments WHERE booking_id IN (SELECT id FROM bookings WHERE customer_name LIKE 'Test Walkin%')")
    cur.execute("DELETE FROM bookings WHERE customer_name LIKE 'Test Walkin%'")
    commit_db()

    today_str = date.today().isoformat()
    two_days_later = (date.today() + timedelta(days=2)).isoformat()
    now_time = datetime.now().strftime("%H:%M")

    # Count users before walkin
    cur.execute("SELECT COUNT(*) AS c FROM users")
    users_before = cur.fetchone()['c']

    # TEST CASE 1: Pure Walk-in (No Account)
    print("\n--- TEST CASE 1: Pure Walk-in (No account) ---")
    payload1 = {
        "vehicle_id": v_id,
        "is_existing_account": False,
        "customer_name": "Test Walkin Guest",
        "customer_phone": "09181112222",
        "customer_address": "Quezon City, Metro Manila",
        "start_date": today_str,
        "start_time": now_time,
        "end_date": two_days_later,
        "end_time": now_time,
        "rental_type": "Self Drive",
        "pickup_location": "Main Office",
        "amount_paid": 4000.00,
        "payment_method": "Cash",
        "status": "Picked Up"
    }
    res1 = client.post('/api/admin/bookings/walkin', json=payload1, headers=headers)
    print("Response status:", res1.status_code, res1.get_json())
    assert res1.status_code == 201, f"Expected 201, got {res1.status_code}: {res1.get_json()}"
    data1 = res1.get_json()
    b_id1 = data1['booking_id']

    # Verify no new user was created in users table
    cur.execute("SELECT COUNT(*) AS c FROM users")
    users_after = cur.fetchone()['c']
    assert users_before == users_after, "Users count MUST NOT increase for pure walk-in!"
    print("[PASS] No new user was generated in users table.")

    # Verify booking in DB has user_id = None
    cur.execute("SELECT id, user_id, customer_name, customer_phone, status, total_price, amount_paid FROM bookings WHERE id = %s", (b_id1,))
    b_row = cur.fetchone()
    print("Database record for walkin #1:", b_row)
    assert b_row['user_id'] is None, "user_id should be NULL!"
    assert b_row['customer_name'] == "Test Walkin Guest"
    assert b_row['status'] == "Picked Up"
    print("[PASS] Walk-in booking saved with user_id = NULL and correct customer info.")

    # Verify payments record created
    cur.execute("SELECT id, booking_id, amount, method, status FROM payments WHERE booking_id = %s", (b_id1,))
    pay_row = cur.fetchone()
    print("Payment record created:", pay_row)
    assert pay_row and float(pay_row['amount']) == 4000.00
    assert pay_row['method'] == 'Cash'
    print("[PASS] Counter payment record recorded.")

    # TEST CASE 2: Overlap collision guard
    print("\n--- TEST CASE 2: Overlap guard ---")
    res_conflict = client.post('/api/admin/bookings/walkin', json=payload1, headers=headers)
    print("Conflict response status:", res_conflict.status_code, res_conflict.get_json())
    assert res_conflict.status_code == 409, "Should reject overlap with 409!"
    print("[PASS] Overlap conflict properly prevented.")

    # TEST CASE 3: Walk-in linked to existing customer account
    print("\n--- TEST CASE 3: Walk-in linked to existing customer account ---")
    # Find a customer account
    cur.execute("SELECT id, full_name, email FROM users WHERE role = 'customer' LIMIT 1")
    cust = cur.fetchone()
    assert cust, "Must have at least 1 customer"
    cust_id = cust['id']

    # Choose vehicle 2 if available, or clean up booking 1 first
    cur.execute("DELETE FROM payments WHERE booking_id = %s", (b_id1,))
    cur.execute("DELETE FROM bookings WHERE id = %s", (b_id1,))
    commit_db()

    payload2 = {
        "vehicle_id": v_id,
        "is_existing_account": True,
        "user_id": cust_id,
        "start_date": today_str,
        "start_time": now_time,
        "end_date": two_days_later,
        "end_time": now_time,
        "rental_type": "Self Drive",
        "pickup_location": "Main Office",
        "amount_paid": 2000.00,
        "status": "Confirmed"
    }
    res2 = client.post('/api/admin/bookings/walkin', json=payload2, headers=headers)
    print("Response status for existing account walk-in:", res2.status_code, res2.get_json())
    assert res2.status_code == 201
    data2 = res2.get_json()
    b_id2 = data2['booking_id']

    cur.execute("SELECT id, user_id, customer_name, status FROM bookings WHERE id = %s", (b_id2,))
    b_row2 = cur.fetchone()
    print("Database record for walkin #2 (linked):", b_row2)
    assert b_row2['user_id'] == cust_id, f"user_id should be {cust_id}!"
    print(f"[PASS] Successfully linked booking to existing customer #{cust_id} ({cust['full_name']})!")

    # Cleanup test booking 2
    cur.execute("DELETE FROM payments WHERE booking_id = %s", (b_id2,))
    cur.execute("DELETE FROM bookings WHERE id = %s", (b_id2,))
    commit_db()
    print("\n[ALL 3 INTEGRATION TEST CASES PASSED WITH 100% SUCCESS!]")
