#!/usr/bin/env python3
"""
Check for recent license uploads and test the upload process
"""
import requests
import json
from datetime import datetime

def check_license_uploads():
    """Check the license details with full URLs and timestamps"""
    
    url = "https://autoride-booking-system.vercel.app/api/user/license-details?user_id=40"
    
    print("Checking for recent license uploads:")
    print("=" * 50)
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data:
                license_data = data['data']
                
                # Show full URLs and timestamps
                print("License record details:")
                print(f"- ID: {license_data.get('id')}")
                print(f"- User ID: {license_data.get('user_id')}")
                print(f"- Created: {license_data.get('created_at')}")
                print(f"- Updated: {license_data.get('updated_at')}")
                
                # Show full URLs
                front_url = license_data.get('license_front_url', '')
                back_url = license_data.get('license_back_url', '')
                
                print(f"\nFull URLs:")
                print(f"Front: {front_url}")
                print(f"Back: {back_url}")
                
                # Extract timestamps from URLs (if present)
                if 'license_front_40_' in front_url:
                    timestamp = front_url.split('license_front_40_')[1].split('.')[0]
                    try:
                        upload_time = datetime.fromtimestamp(int(timestamp))
                        print(f"\nFront image upload time: {upload_time}")
                    except:
                        print(f"\nFront image timestamp: {timestamp}")
                
                if 'license_back_40_' in back_url:
                    timestamp = back_url.split('license_back_40_')[1].split('.')[0]
                    try:
                        upload_time = datetime.fromtimestamp(int(timestamp))
                        print(f"Back image upload time: {upload_time}")
                    except:
                        print(f"Back image timestamp: {timestamp}")
                
                # Test the URLs
                print(f"\nURL Status Tests:")
                for name, url in [("Front", front_url), ("Back", back_url)]:
                    if url:
                        try:
                            test_resp = requests.head(url, timeout=10)
                            print(f"{name}: {test_resp.status_code}")
                            if test_resp.status_code != 200:
                                print(f"  ? {name} image not accessible")
                            else:
                                print(f"  ? {name} image OK")
                        except Exception as e:
                            print(f"{name}: Error - {e}")
                    else:
                        print(f"{name}: No URL")
                
                # Check when record was last updated
                updated_at = license_data.get('updated_at')
                if updated_at:
                    print(f"\nRecord last updated: {updated_at}")
                    print("?? If you just uploaded, the update time should be very recent")
                
            else:
                print("? No license data found")
                
        else:
            print(f"? API Error: {response.status_code}")
            
    except Exception as e:
        print(f"? Request failed: {e}")

if __name__ == "__main__":
    check_license_uploads()