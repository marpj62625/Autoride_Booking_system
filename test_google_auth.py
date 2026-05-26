#!/usr/bin/env python3
"""
Test script for Google Auth endpoint
This simulates what the mobile app sends to the backend
"""

import requests
import json

# Test configuration
API_URL = "https://autoride-booking-system.vercel.app/api/auth/google"
# API_URL = "http://localhost:5000/api/auth/google"  # For local testing

# This is a MOCK token for testing - in real app, this comes from Google
test_payload = {
    "id_token": "mock_token_for_testing",
    "email": "test@gmail.com",
    "name": "Test User"
}

print("Testing Google Auth Endpoint")
print("=" * 50)
print(f"URL: {API_URL}")
print(f"Payload: {json.dumps(test_payload, indent=2)}")
print("=" * 50)

try:
    response = requests.post(
        API_URL,
        json=test_payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code in [200, 201]:
        print("\n? Endpoint is responding correctly!")
        data = response.json()
        if "user" in data:
            print("? Response has 'user' object")
            user = data["user"]
            required_fields = ["id", "fullName", "email", "isDriver", "isVerified"]
            for field in required_fields:
                if field in user:
                    print(f"? User has '{field}' field: {user[field]}")
                else:
                    print(f"? User missing '{field}' field")
        else:
            print("? Response missing 'user' object")
    else:
        print(f"\n?? Endpoint returned error: {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"\n? Request failed: {e}")
except Exception as e:
    print(f"\n? Error: {e}")

print("\n" + "=" * 50)
print("Note: This test uses a mock token.")
print("Real tokens come from Google Sign-In in the mobile app.")
print("Expected error: 'Invalid Google token' (401)")
print("=" * 50)
