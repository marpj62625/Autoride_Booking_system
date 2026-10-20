import sys
sys.path.insert(0, 'backend')
from app import app
from database import get_cursor

client = app.test_client()

with app.app_context():
    cur = get_cursor()
    # Find a customer user
    cur.execute("SELECT id, email, is_verified FROM users WHERE role = 'customer' AND is_verified = 2 LIMIT 1")
    user = cur.fetchone()
    # Find an available vehicle
    cur.execute("SELECT id, brand, model, daily_rate FROM vehicles WHERE status = 'Available' LIMIT 1")
    veh = cur.fetchone()

print("Customer User:", user)
print("Vehicle:", veh)

if user and veh:
    # Test booking creation
    payload = {
        "user_id": user['id'],
        "vehicle_id": veh['id'],
        "start_date": "2026-11-20",
        "end_date": "2026-11-23",
        "pickup_location": "Bacolod Main Branch",
        "rental_type": "Self Drive",
        "addons": [],
        "pickup_province": "Negros Occidental",
        "pickup_municipality": "Bacolod City",
        "pickup_barangay": "Barangay 1",
        "return_province": "Negros Occidental",
        "return_municipality": "Bacolod City",
        "return_barangay": "Barangay 1",
        "pickup_time": "08:00",
        "return_time": "08:00",
        "service_type": "pickup",
        "payment_type": "Full"
    }
    
    res = client.post('/api/book', json=payload)
    print("Booking response status:", res.status_code)
    print("Booking response data:", res.get_json())
    
    if res.status_code == 201:
        bid = res.get_json().get('booking_id')
        print(f"Created test booking #{bid} successfully!")
        
        # Verify in DB
        with app.app_context():
            cur = get_cursor()
            cur.execute("SELECT id, total_price, base_price, status FROM bookings WHERE id = %s", (bid,))
            row = cur.fetchone()
            print("DB booking record:", row)
            
            # Clean up test booking
            cur.execute("DELETE FROM bookings WHERE id = %s", (bid,))
            cur.execute("UPDATE vehicles SET status = 'Available' WHERE id = %s", (veh['id'],))
            from database import commit_db
            commit_db()
            print("Cleaned up test booking.")
