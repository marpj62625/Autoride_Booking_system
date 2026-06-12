#!/usr/bin/env python3
"""
Test script to verify license image fallback implementation
"""
import requests
import json

# Test the license-details endpoint
def test_license_details(user_id=40):
    """Test the license-details endpoint to verify fallback data is included"""
    
    base_url = "https://autoride-booking-system.vercel.app"
    # base_url = "http://localhost:5000"  # For local testing
    
    url = f"{base_url}/api/user/license-details?user_id={user_id}"
    
    print(f"Testing license-details endpoint for user {user_id}")
    print(f"URL: {url}")
    print("-" * 50)
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response structure:")
            print(json.dumps(data, indent=2, default=str))
            
            # Check if we have the fallback fields
            if 'data' in data:
                license_data = data['data']
                print("\nFallback fields check:")
                print(f"- license_front_url: {license_data.get('license_front_url', 'MISSING')}")
                print(f"- license_back_url: {license_data.get('license_back_url', 'MISSING')}")
                print(f"- license_image_url: {license_data.get('license_image_url', 'MISSING')}")
                
                # Test fallback logic
                front_fallback = license_data.get('license_front_url') or license_data.get('license_image_url') or ''
                print(f"\nFallback result (front): '{front_fallback}'")
                
                if front_fallback:
                    print("? Fallback pattern working - has image URL")
                else:
                    print("? No image URL available (neither front nor fallback)")
            else:
                print("?? No 'data' field in response")
        else:
            print(f"? Error response: {response.text}")
            
    except Exception as e:
        print(f"? Request failed: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_license_details(40)  # Test with user ID 40 as mentioned in context