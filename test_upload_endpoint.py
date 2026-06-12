#!/usr/bin/env python3
"""
Test the license upload endpoint to debug the Supabase issue
"""
import requests
import json
from datetime import datetime

def test_upload_endpoint():
    """Test the license upload functionality"""
    
    # Create a simple test image file (minimal PNG)
    test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDAT\x08\x1dc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\nIEND\xaeB`\x82'
    
    url = "https://autoride-booking-system.vercel.app/api/user/license-details"
    
    print("Testing license upload endpoint:")
    print(f"URL: {url}")
    print("-" * 50)
    
    # Test data
    files = {
        'license_front_file': ('test_front.png', test_image_data, 'image/png'),
        'license_back_file': ('test_back.png', test_image_data, 'image/png')
    }
    
    data = {
        'user_id': '40',
        'full_name': 'Test Upload',
        'license_number': 'TEST-123',
        'expiry_date': '2025-12-31',
        'license_class': 'B',
        'issuing_country_state': 'Philippines',
        'emergency_contact_name': 'Test Contact',
        'emergency_contact_phone': '09123456789',
        'emergency_contact_relationship': 'Friend'
    }
    
    try:
        print("Sending upload request...")
        response = requests.post(url, files=files, data=data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n? Upload request succeeded!")
            
            # Now test if the new URLs work
            print("Testing if new upload is accessible...")
            import time
            time.sleep(2)  # Wait a moment for processing
            
            # Check the updated record
            test_resp = requests.get(f"https://autoride-booking-system.vercel.app/api/user/license-details?user_id=40")
            if test_resp.status_code == 200:
                data = test_resp.json()
                if 'data' in data:
                    license_data = data['data']
                    
                    print(f"Updated record timestamp: {license_data.get('updated_at')}")
                    
                    front_url = license_data.get('license_front_url', '')
                    back_url = license_data.get('license_back_url', '')
                    
                    print(f"New front URL: {front_url[:100]}...")
                    print(f"New back URL: {back_url[:100]}...")
                    
                    # Test the new URLs
                    for name, url_test in [("Front", front_url), ("Back", back_url)]:
                        if url_test:
                            try:
                                img_resp = requests.head(url_test, timeout=10)
                                print(f"{name} image status: {img_resp.status_code}")
                                if img_resp.status_code == 200:
                                    print(f"  ? {name} upload SUCCESS!")
                                else:
                                    print(f"  ? {name} still broken after upload")
                            except Exception as e:
                                print(f"  ? {name} test error: {e}")
            
        else:
            print("? Upload failed!")
            print("This could indicate:")
            print("- Supabase configuration issue")
            print("- File upload endpoint problem") 
            print("- Authentication/permission issue")
            
    except Exception as e:
        print(f"? Upload test failed: {e}")

def check_supabase_bucket():
    """Test if we can access Supabase storage directly"""
    
    print("\nTesting Supabase bucket accessibility:")
    print("-" * 40)
    
    # Test a few different URL patterns to see what works
    test_urls = [
        "https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/",
        "https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/bucket/uploads",
        "https://fydfsgjrlowrrtlmefwq.supabase.co/rest/v1/"
    ]
    
    for url in test_urls:
        try:
            resp = requests.get(url, timeout=10)
            print(f"{url} ? {resp.status_code}")
        except Exception as e:
            print(f"{url} ? Error: {e}")

if __name__ == "__main__":
    test_upload_endpoint()
    check_supabase_bucket()