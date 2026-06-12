#!/usr/bin/env python3
import requests
import json

url = "https://autoride-booking-system.vercel.app/api/user/license-details"
params = {"user_id": "40"}

print(f"Testing: {url}")
print(f"Parameters: {params}")
print("-" * 50)

try:
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response Body:")
    
    try:
        json_response = response.json()
        print(json.dumps(json_response, indent=2))
    except:
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")

# Test with different user_ids
for user_id in ["1", "100", "", " ", "abc", "0", "-1"]:
    print(f"\n" + "="*50)
    print(f"Testing with user_id: '{user_id}'")
    try:
        response = requests.get(url, params={"user_id": user_id})
        print(f"Status: {response.status_code}")
        try:
            json_response = response.json()
            print(f"Response: {json.dumps(json_response, indent=2)}")
        except:
            print(f"Response Text: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")