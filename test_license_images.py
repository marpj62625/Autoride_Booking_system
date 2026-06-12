#!/usr/bin/env python3
import requests
import json

# Test the license API response
print("=== TESTING LICENSE DETAILS API ===")
url = "https://autoride-booking-system.vercel.app/api/user/license-details?user_id=40"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    license_data = data.get('data', {})
    
    print(f"API Status: {response.status_code}")
    print(f"License Number: {license_data.get('license_number', 'N/A')}")
    print(f"Full Name: {license_data.get('full_name', 'N/A')}")
    
    front_url = license_data.get('license_front_url', '')
    back_url = license_data.get('license_back_url', '')
    
    print(f"\n=== LICENSE IMAGE URLS ===")
    print(f"Front URL: {front_url}")
    print(f"Back URL: {back_url}")
    
    # Test if image URLs are accessible
    print(f"\n=== TESTING IMAGE ACCESSIBILITY ===")
    
    if front_url:
        print(f"Testing front image: {front_url[:80]}...")
        try:
            img_response = requests.get(front_url, timeout=10)
            print(f"Front image status: {img_response.status_code}")
            if img_response.status_code == 200:
                print(f"Front image size: {len(img_response.content)} bytes")
                print(f"Front image content-type: {img_response.headers.get('content-type', 'unknown')}")
            else:
                print(f"Front image error: {img_response.text[:200]}")
        except Exception as e:
            print(f"Front image request failed: {e}")
    
    if back_url:
        print(f"\nTesting back image: {back_url[:80]}...")
        try:
            img_response = requests.get(back_url, timeout=10)
            print(f"Back image status: {img_response.status_code}")
            if img_response.status_code == 200:
                print(f"Back image size: {len(img_response.content)} bytes")
                print(f"Back image content-type: {img_response.headers.get('content-type', 'unknown')}")
            else:
                print(f"Back image error: {img_response.text[:200]}")
        except Exception as e:
            print(f"Back image request failed: {e}")
else:
    print(f"API Error: {response.status_code}")
    print(response.text)