#!/usr/bin/env python3
"""
Test script for push notifications
Usage: python test_push_notifications.py <user_id>
"""
import sys
import requests

API_BASE = 'https://autoride-booking-system.vercel.app/api'

def test_push_notification(user_id):
    """Send a test push notification to a user"""
    url = f'{API_BASE}/test-push/{user_id}'
    
    data = {
        'title': 'Test Refund Notification',
        'message': f'Your refund of PHP 1,500.00 has been processed via GCash. Reference: TEST123456'
    }
    
    try:
        response = requests.post(url, json=data)
        
        if response.ok:
            print(f"? Push notification sent successfully to user {user_id}")
            print(f"Response: {response.json()}")
        else:
            print(f"? Failed to send push notification: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"? Network error: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python test_push_notifications.py <user_id>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    try:
        user_id = int(user_id)
        test_push_notification(user_id)
    except ValueError:
        print("Error: user_id must be a number")
        sys.exit(1)