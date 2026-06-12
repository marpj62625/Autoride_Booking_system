#!/usr/bin/env python3
"""
Test the live API to verify if backend changes were deployed
"""
import requests
import json

def test_live_license_api():
    """Test if the deployed API includes the license_image_url fallback field"""
    
    # Test the deployed API
    url = "https://autoride-booking-system.vercel.app/api/user/license-details?user_id=40"
    
    print("Testing LIVE deployed API:")
    print(f"URL: {url}")
    print("-" * 60)
    
    try:
        response = requests.get(url, timeout=15)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if our backend change is deployed
            if 'data' in data and 'license_image_url' in data['data']:
                print("? BACKEND CHANGE DEPLOYED!")
                print(f"   license_image_url field: '{data['data']['license_image_url']}'")
            else:
                print("? Backend change NOT deployed yet")
                print("   Missing license_image_url field in response")
            
            # Show current license URLs
            if 'data' in data:
                license_data = data['data']
                print(f"\nCurrent license URLs:")
                print(f"- license_front_url: {license_data.get('license_front_url', 'MISSING')}")
                print(f"- license_back_url: {license_data.get('license_back_url', 'MISSING')}")
                print(f"- license_image_url: {license_data.get('license_image_url', 'MISSING')}")
                
                # Test fallback logic
                front_url = license_data.get('license_front_url') or license_data.get('license_image_url') or ''
                print(f"\nFallback result: '{front_url}'")
                
                if front_url:
                    # Test if URL works
                    try:
                        img_test = requests.head(front_url, timeout=5)
                        print(f"Image URL status: {img_test.status_code}")
                    except:
                        print("Image URL test failed")
            
            # Check deployment timestamp info
            deployment_info = data.get('debug', {})
            print(f"\nDeployment info: {deployment_info}")
            
        else:
            print(f"? API Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"? Request failed: {e}")

if __name__ == "__main__":
    test_live_license_api()