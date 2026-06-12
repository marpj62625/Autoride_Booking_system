#!/usr/bin/env python3
"""
Check what's in the users table for license_image_url fallback
"""
import requests
import json

def check_user_profile(user_id=40):
    """Check the user profile endpoint to see if license_image_url exists"""
    
    base_url = "https://autoride-booking-system.vercel.app"
    url = f"{base_url}/api/profile?user_id={user_id}"
    
    print(f"Checking user profile for user {user_id}")
    print(f"URL: {url}")
    print("-" * 50)
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Profile data:")
            print(json.dumps(data, indent=2, default=str))
            
            # Look for license image fields
            license_image = data.get('license_image')
            license_image_url = data.get('license_image_url') 
            
            print(f"\nLicense fields in users table:")
            print(f"- license_image: {license_image}")
            print(f"- license_image_url: {license_image_url}")
            
            if license_image_url:
                print(f"\n? Found license_image_url fallback!")
                print(f"Testing fallback URL: {license_image_url}")
                
                # Test if fallback URL works
                try:
                    img_response = requests.head(license_image_url, timeout=10)
                    if img_response.status_code == 200:
                        print("? Fallback URL works!")
                    else:
                        print(f"? Fallback URL also broken: {img_response.status_code}")
                except Exception as e:
                    print(f"? Fallback URL test failed: {e}")
            else:
                print("? No license_image_url in users table")
                
        else:
            print(f"? Profile request failed: {response.text}")
            
    except Exception as e:
        print(f"? Request failed: {e}")

if __name__ == "__main__":
    check_user_profile(40)