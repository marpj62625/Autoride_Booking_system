import requests
import json
import random

BASE_URL = "http://localhost:9999"

def test_full_payment_flow():
    try:
        # 1. Create a dummy Booking
        print("Step 1: Creating a test booking...")
        booking_payload = {
            "user_id": 14, # Using verified user ID from previous sessions
            "vehicle_id": 1, # Toyota Vios
            "start_date": "2026-05-01",
            "end_date": "2026-05-05",
            "pickup_location": "Manila",
            "total_price": 10000.00,
            "rental_type": "Self-Drive"
        }
        
        book_res = requests.post(f"{BASE_URL}/book", json=booking_payload)
        if book_res.status_code != 201:
            print(f"FAILED to create booking: {book_res.text}")
            return
        
        booking_id = book_res.json().get('booking_id')
        print(f"SUCCESS! Created Booking ID: {booking_id}")

        # 2. Process Payment for that booking
        print(f"\nStep 2: Simulating payment for Booking {booking_id}...")
        ref_num = 'TEST-' + str(random.randint(10000, 99999))
        payment_payload = {
            "booking_id": booking_id,
            "amount": 10000.00,
            "method": "Credit Card",
            "reference_number": ref_num
        }
        
        # Testing JSON delivery first
        pay_res = requests.post(f"{BASE_URL}/payment", json=payment_payload)
        
        if pay_res.status_code == 200:
            print(f"SUCCESS! Payment processed. Status: {pay_res.json().get('status')}")
            print(f"Reference Number: {ref_num}")
            print("\nVERIFICATION COMPLETE: Flow is working end-to-end!")
        else:
            print(f"FAILED to process payment: {pay_res.text}")

    except Exception as e:
        print(f"CONNECTION ERROR: {str(e)}")
        print("TIP: Make sure your Flask server is RUNNING on http://localhost:9999")

if __name__ == "__main__":
    test_full_payment_flow()
