#!/usr/bin/env python3
"""
Check what license data the admin endpoint returns for comparison
"""
import requests
import json

def check_admin_license_data(user_id=40):
    """Check the admin license-details endpoint to see what data it returns"""
    
    base_url = "https://autoride-booking-system.vercel.app"
    url = f"{base_url}/api/admin/users/{user_id}/license-details"
    
    print(f"Checking admin license-details for user {user_id}")
    print(f"URL: {url}")
    print("-" * 50)
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Admin license data:")
            print(json.dumps(data, indent=2, default=str))
            
            # Check license image fields
            license_front_url = data.get('license_front_url')
            license_image_url = data.get('license_image_url') 
            license_image = data.get('license_image')
            
            print(f"\nLicense fields from admin endpoint:")
            print(f"- license_front_url: {license_front_url}")
            print(f"- license_image_url: {license_image_url}") 
            print(f"- license_image: {license_image}")
            
            # Test any available URLs
            for name, url_val in [("license_front_url", license_front_url), ("license_image_url", license_image_url), ("license_image", license_image)]:
                if url_val:
                    print(f"\nTesting {name}: {url_val[:100]}...")
                    try:
                        img_response = requests.head(url_val, timeout=10)
                        print(f"? {name} status: {img_response.status_code}")
                    except Exception as e:
                        print(f"? {name} test failed: {e}")
                        
        else:
            print(f"? Admin request failed: {response.text}")
            
    except Exception as e:
        print(f"? Request failed: {e}")

if __name__ == "__main__":
    check_admin_license_data(40)