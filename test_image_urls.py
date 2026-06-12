#!/usr/bin/env python3
"""
Test the actual license image URLs to see if they return 404 or work
"""
import requests

def test_image_url(url):
    """Test if an image URL returns valid content or 404"""
    try:
        # Only test first 100 chars for display
        display_url = url[:100] + "..." if len(url) > 100 else url
        print(f"Testing: {display_url}")
        
        response = requests.head(url, timeout=10)  # Use HEAD to avoid downloading the full image
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            content_length = response.headers.get('content-length', 'unknown')
            print(f"? Image OK - Type: {content_type}, Size: {content_length} bytes")
            return True
        else:
            print(f"? Image broken - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"? Request failed: {e}")
        return False

if __name__ == "__main__":
    # Test the URLs from the API response
    front_url = "https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/license_front_40_1781260829.jpg"
    back_url = "https://fydfsgjrlowrrtlmefwq.supabase.co/storage/v1/object/public/uploads/license_back_40_1781260850.jpg"
    
    print("Testing license image URLs from Supabase:")
    print("=" * 60)
    
    print("\n1. Front License Image:")
    front_ok = test_image_url(front_url)
    
    print("\n2. Back License Image:")  
    back_ok = test_image_url(back_url)
    
    print(f"\nSummary:")
    print(f"- Front image working: {front_ok}")
    print(f"- Back image working: {back_ok}")
    
    if not front_ok and not back_ok:
        print("\n?? Both images are broken - this explains why license images aren't showing!")
        print("?? Need to implement fallback to users.license_image_url")