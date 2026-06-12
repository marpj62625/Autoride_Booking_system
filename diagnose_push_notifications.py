#!/usr/bin/env python3
"""
Diagnose Push Notification Issues
Run this to check what's causing push notification failures
"""
import requests
import sys

API_BASE = 'https://autoride-booking-system.vercel.app/api'

def diagnose_fcm_config():
    """Check FCM configuration"""
    print("?? Diagnosing FCM Configuration...")
    
    try:
        response = requests.get(f'{API_BASE}/test-fcm-config')
        
        if response.ok:
            data = response.json()
            config = data.get('config', {})
            
            print("?? FCM Configuration Status:")
            print(f"  ? Server Key Configured: {config.get('fcm_server_key_configured')}")
            print(f"  ? Server Key Length: {config.get('fcm_server_key_length')} chars")
            print(f"  ? Server Key Preview: {config.get('fcm_server_key_preview')}")
            print(f"  ? Environment Variable: {config.get('environment_fcm_key')}")
            print(f"  ? V1 API Token: {config.get('fcm_v1_api_token')}")
            
            if config.get('fcm_v1_api_error'):
                print(f"  ??  V1 API Error: {config.get('fcm_v1_api_error')}")
                
            if config.get('fcm_service_error'):
                print(f"  ? FCM Service Error: {config.get('fcm_service_error')}")
                
            return config.get('fcm_server_key_configured', False)
        else:
            print(f"? Failed to get FCM config: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"? Network error checking FCM config: {e}")
        return False

def test_push_notification(user_id):
    """Test sending push notification"""
    print(f"\n?? Testing Push Notification to User {user_id}...")
    
    url = f'{API_BASE}/test-push/{user_id}'
    
    data = {
        'title': 'Autoride Test Notification',
        'message': 'Testing push notifications system! If you receive this, it\'s working! ??'
    }
    
    try:
        response = requests.post(url, json=data)
        
        if response.ok:
            print("? Push notification API call succeeded!")
            result = response.json()
            print(f"   Response: {result.get('message')}")
            return True
        else:
            print(f"? Push notification failed: {response.status_code}")
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"   Error: {error_data}")
            return False
            
    except Exception as e:
        print(f"? Network error sending push: {e}")
        return False

def main():
    print("?? Autoride Push Notification Diagnostics")
    print("=" * 50)
    
    # Step 1: Check FCM Configuration
    fcm_ok = diagnose_fcm_config()
    
    # Step 2: Test push notification if user provided
    if len(sys.argv) >= 2:
        try:
            user_id = int(sys.argv[1])
            push_ok = test_push_notification(user_id)
        except ValueError:
            print(f"\n? Invalid user_id: {sys.argv[1]} (must be a number)")
            push_ok = False
    else:
        print(f"\n?? To test push notification to a user:")
        print(f"   python {sys.argv[0]} <user_id>")
        push_ok = None
    
    # Summary
    print("\n" + "=" * 50)
    print("?? DIAGNOSIS SUMMARY")
    print("=" * 50)
    
    if fcm_ok:
        print("? FCM Configuration: OK")
    else:
        print("? FCM Configuration: NEEDS SETUP")
        print("   ?? Follow FIREBASE_SETUP_GUIDE.md to configure Firebase")
    
    if push_ok is True:
        print("? Push Notifications: WORKING")
    elif push_ok is False:
        print("? Push Notifications: NOT WORKING")
        print("   ?? Check FCM configuration and user FCM token")
    else:
        print("? Push Notifications: NOT TESTED")
        
    print("\n?? Next Steps:")
    if not fcm_ok:
        print("1. Create Firebase project (5 minutes)")
        print("2. Get server key from Firebase Console")  
        print("3. Update FCM_SERVER_KEY in backend/config.py")
        print("4. Rebuild APK and test again")
    elif push_ok is False:
        print("1. Check if user has registered FCM token")
        print("2. Verify Firebase project settings")
        print("3. Check backend logs for detailed error messages")
    else:
        print("1. Install latest APK on device")
        print("2. Login and register for notifications")
        print("3. Test push notifications")

if __name__ == '__main__':
    main()