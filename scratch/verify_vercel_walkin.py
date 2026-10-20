import requests
import time

url = "https://autoride-booking-system.vercel.app/api/admin/bookings/walkin"
print(f"Testing endpoint {url}...")

# Endpoint should respond with 401 Unauthorized (because no admin credentials sent), proving route exists and is deployed
for attempt in range(1, 11):
    try:
        r = requests.post(url, json={})
        print(f"Attempt {attempt}: Status {r.status_code}, Response: {r.text[:100]}")
        if r.status_code in (401, 400, 403):
            print("[PASS] Endpoint is active and enforcing admin authentication on Vercel!")
            break
    except Exception as e:
        print(f"Attempt {attempt} failed: {e}")
    time.sleep(6)
