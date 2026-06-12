#!/usr/bin/env python3
import requests
import json

print("=== CHECKING OLD LICENSE SYSTEM ===")

# Check user profile-full endpoint (may include license_image_url)
url = "https://autoride-booking-system.vercel.app/api/user/profile-full?user_id=40"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    print(f"Profile API Status: {response.status_code}")
    print(f"Profile Data:")
    print(json.dumps(data, indent=2))
    
    # Check if may license_image_url
    license_image_url = data.get('license_image_url', '')
    if license_image_url:
        print(f"\n=== OLD LICENSE IMAGE FOUND ===")
        print(f"License Image URL: {license_image_url}")
        
        # Test if accessible
        print(f"\nTesting old license image accessibility...")
        try:
            img_response = requests.get(license_image_url, timeout=10)
            print(f"Old license image status: {img_response.status_code}")
            if img_response.status_code == 200:
                print(f"Old license image size: {len(img_response.content)} bytes")
                print(f"Old license image content-type: {img_response.headers.get('content-type', 'unknown')}")
            else:
                print(f"Old license image error: {img_response.text[:200]}")
        except Exception as e:
            print(f"Old license image request failed: {e}")
    else:
        print("No old license_image_url found")
else:
    print(f"Profile API Error: {response.status_code}")
    print(response.text)