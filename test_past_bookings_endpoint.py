"""
Test script to verify the /api/bookings/past endpoint is accessible
"""
import requests

# Test the endpoint
base_url = "http://localhost:5000"  # Adjust if your server runs on a different port
endpoint = f"{base_url}/api/bookings/past"

print(f"Testing endpoint: {endpoint}")
print("-" * 50)

try:
    # Test with default parameters
    response = requests.get(endpoint, params={
        'page': 1,
        'page_size': 10,
        'sort_by': 'completion_date_desc'
    })
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("\n? Endpoint is working correctly!")
    else:
        print(f"\n? Endpoint returned error: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("? Could not connect to server. Is the Flask server running?")
    print("   Start the server with: python backend/app.py")
except Exception as e:
    print(f"? Error: {str(e)}")
