import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:9999"
DATE_TODAY = datetime.now().strftime("%Y-%m-%d")

def test_admin_reports():
    endpoints = [
        f"/reports/summary?period=daily&date={DATE_TODAY}",
        f"/reports/revenue?period=daily&date={DATE_TODAY}",
        "/reports/booking-status",
        f"/reports/bookings-trend?period=daily&date={DATE_TODAY}",
        "/reports/top-vehicles"
    ]
    
    print(f"Starting Admin Reports Verification for date: {DATE_TODAY}\n")
    
    all_passed = True
    for ep in endpoints:
        try:
            print(f"Testing {ep}...")
            res = requests.get(f"{BASE_URL}{ep}")
            if res.status_code == 200:
                print(f"[OK] SUCCESS! Data: {json.dumps(res.json())[:80]}...")
            else:
                print(f"[ERROR] FAILED! Status: {res.status_code}, Error: {res.text}")
                all_passed = False
        except Exception as e:
            print(f"[CONN ERROR] CONNECTION ERROR on {ep}: {str(e)}")
            all_passed = False
            
    if all_passed:
        print("\n[SUCCESS] ALL REPORT ENDPOINTS ARE FULLY FUNCTIONAL!")
    else:
        print("\n[WARNING] Some endpoints failed. Please ensure the server is running and the database has data.")

if __name__ == "__main__":
    test_admin_reports()
