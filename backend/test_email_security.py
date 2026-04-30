import requests
import json

BASE_URL = "http://localhost:9999"

def test_email_security():
    print("Starting Email Security & Verification Test...\n")
    
    # 1. Test Block non-gmail
    print("Test 1: Attempting to register with @yahoo.com...")
    bad_payload = {
        "name": "Spammer",
        "email": "spammer@yahoo.com",
        "password": "password123"
    }
    res = requests.post(f"{BASE_URL}/register", json=bad_payload)
    if res.status_code == 400:
        print(f"SUCCESS: System blocked Yahoo email. Message: {res.json().get('error')}")
    else:
        print(f"FAILED: System allowed Yahoo email. Status: {res.status_code}")

    # 2. Test Allow gmail and Check OTP
    print("\nTest 2: Attempting to register with @gmail.com...")
    test_email = "tester_antigravity@gmail.com"
    good_payload = {
        "name": "Legit User",
        "email": test_email,
        "password": "password123"
    }
    res = requests.post(f"{BASE_URL}/register", json=good_payload)
    if res.status_code == 201:
        print("SUCCESS: Registered Gmail account. Check your BACKEND TERMINAL for the OTP code!")
    elif res.status_code == 409:
        print("INFO: Email already exists, skipping registration test.")
    else:
        print(f"FAILED: Could not register Gmail. Status: {res.status_code}, Error: {res.text}")

    # 3. Test Login without verification
    print("\nTest 3: Attempting to login BEFORE verification...")
    login_res = requests.post(f"{BASE_URL}/login", json={"email": test_email, "password": "password123"})
    if login_res.status_code == 403:
        print(f"SUCCESS: Login blocked. Message: {login_res.json().get('error')}")
    else:
        print(f"FAILED: System allowed login without verification. Status: {login_res.status_code}")

    print("\nMANUAL ACTION REQUIRED:")
    print("1. Look at your Flask Terminal.")
    print(f"2. Find the 6-digit code for {test_email}.")
    print("3. Use the website or a POST request to /auth/verify-email to finish.")

if __name__ == "__main__":
    test_email_security()
