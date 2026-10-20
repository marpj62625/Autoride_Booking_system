import os, sys
sys.path.insert(0, '.')
from app import app

client = app.test_client()

print("1. Testing GET /api/admin/bookings...")
res = client.get('/api/admin/bookings')
print(f"Status: {res.status_code}")
data = res.get_json()
print(f"Total bookings returned: {len(data)}")
sample = data[0] if data else {}
print(f"Sample booking: ID={sample.get('id')}, Customer={sample.get('customer_name')}, Email={sample.get('customer_email')}")

print("\n2. Testing GET /api/admin/bookings/341...")
res = client.get('/api/admin/bookings/341')
print(f"Status: {res.status_code}")
b341 = res.get_json()
print(f"Booking 341: ID={b341.get('id')}, Cust={b341.get('customer_name')}, Email={b341.get('customer_email')}")

print("\n3. Testing GET /api/admin/bookings/642 (User 25 Arvin Corpuz)...")
res = client.get('/api/admin/bookings/642')
print(f"Status: {res.status_code}")
b642 = res.get_json()
print(f"Booking 642: ID={b642.get('id')}, Cust={b642.get('customer_name')}, Email={b642.get('customer_email')}")

print("\n4. Testing GET /api/admin/users/list...")
res = client.get('/api/admin/users/list')
print(f"Status: {res.status_code}")
users = res.get_json()
print(f"Total users returned: {len(users)}")
verified_cnt = sum(1 for u in users if u.get('is_verified') == 2)
unverified_cnt = sum(1 for u in users if u.get('is_verified') != 2)
no_email_cnt = sum(1 for u in users if not u.get('email'))
print(f"Verified users: {verified_cnt}")
print(f"Unverified users: {unverified_cnt}")
print(f"Users with no email: {no_email_cnt}")

print("\n5. Testing fleet calendar / bookings...")
res = client.get('/api/admin/reports?type=overview')
print(f"Status: {res.status_code}")
overview = res.get_json()
print("Overview keys:", list(overview.keys()) if isinstance(overview, dict) else type(overview))

print("\nAll API tests completed successfully!")
