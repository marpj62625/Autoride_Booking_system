import requests
import json

BASE_URL = "http://localhost:9999"

def test_availability():
    print("--- Testing Availability Logic ---")
    
    # 1. Fetch all vehicles normally
    res_all = requests.get(f"{BASE_URL}/vehicles")
    all_count = len(res_all.json())
    print(f"Total vehicles: {all_count}")
    
    # 2. Find a vehicle to "Book" for testing
    vehicle = res_all.json()[0]
    vid = vehicle['id']
    vname = f"{vehicle['brand']} {vehicle['model']}"
    print(f"Testing with vehicle: {vname} (ID: {vid})")
    
    # 3. Create a mock booking for this vehicle
    # We'll use a date range in the future
    test_start = "2026-12-01"
    test_end = "2026-12-05"
    
    payload = {
        "user_id": 1, 
        "vehicle_id": vid,
        "start_date": test_start,
        "end_date": test_end,
        "pickup_location": "Test Location",
        "rental_type": "Self Drive",
        "status": "Confirmed",
        "total_price": 5000
    }
    
    # Use the /book endpoint (assuming it works and saves to DB)
    res_book = requests.post(f"{BASE_URL}/book", json=payload)
    if res_book.ok:
        print(f"Mock booking created for {vname} from {test_start} to {test_end}")
    else:
        print(f"Failed to create mock booking: {res_book.text}")
        return

    # 4. Search for vehicles overlapping with the booking
    # Overlap search: Dec 3 to Dec 4
    res_overlap = requests.get(f"{BASE_URL}/vehicles", params={
        "start_date": "2026-12-03",
        "end_date": "2026-12-04"
    })
    
    overlap_ids = [v['id'] for v in res_overlap.json()]
    if vid not in overlap_ids:
        print(f"SUCCESS: {vname} (ID: {vid}) was HIDDEN during overlapping dates.")
    else:
        print(f"FAILURE: {vname} (ID: {vid}) was still visible during overlapping dates.")

    # 5. Search for vehicles NOT overlapping
    # No overlap: Dec 10 to Dec 12
    res_no_overlap = requests.get(f"{BASE_URL}/vehicles", params={
        "start_date": "2026-12-10",
        "end_date": "2026-12-12"
    })
    
    no_overlap_ids = [v['id'] for v in res_no_overlap.json()]
    if vid in no_overlap_ids:
        print(f"SUCCESS: {vname} (ID: {vid}) was VISIBLE during non-overlapping dates.")
    else:
        print(f"FAILURE: {vname} (ID: {vid}) was hidden during non-overlapping dates.")

if __name__ == "__main__":
    try:
        test_availability()
    except Exception as e:
        print(f"Error: {e}")
