#!/usr/bin/env python3
"""
Check the admin/users/list endpoint to see what license fields it returns
"""
import requests
import json

def check_admin_users_list():
    """Check the admin users list endpoint to see license_image/license_image_url fields"""
    
    base_url = "https://autoride-booking-system.vercel.app"
    url = f"{base_url}/api/admin/users/list"
    
    print(f"Checking admin users list endpoint")
    print(f"URL: {url}")
    print("-" * 50)
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Find user 40 in the list
            user_40 = None
            for user in data:
                if user.get('id') == 40:
                    user_40 = user
                    break
            
            if user_40:
                print("User 40 from admin users list:")
                print(json.dumps(user_40, indent=2, default=str))
                
                # Check the exact fields admin mobile uses
                license_image = user_40.get('license_image')
                license_image_url = user_40.get('license_image_url')
                
                print(f"\nAdmin mobile fallback fields:")
                print(f"- license_image: {license_image}")
                print(f"- license_image_url: {license_image_url}")
                
                # Test admin mobile fallback logic: v.license_image || v.license_image_url || ''
                fallback_result = license_image or license_image_url or ''
                print(f"- Admin fallback result: '{fallback_result}'")
                
                if fallback_result:
                    print(f"\n? Admin mobile has working license URL!")
                    print(f"Testing: {fallback_result[:100]}...")
                    
                    try:
                        img_response = requests.head(fallback_result, timeout=10)
                        print(f"Status: {img_response.status_code}")
                        if img_response.status_code == 200:
                            print("? Admin mobile license URL works!")
                        else:
                            print(f"? Admin mobile license URL broken: {img_response.status_code}")
                    except Exception as e:
                        print(f"? URL test failed: {e}")
                else:
                    print("? No license URL in admin users list either")
            else:
                print("? User 40 not found in admin users list")
                
        else:
            print(f"? Admin users list request failed: {response.text}")
            
    except Exception as e:
        print(f"? Request failed: {e}")

if __name__ == "__main__":
    check_admin_users_list()