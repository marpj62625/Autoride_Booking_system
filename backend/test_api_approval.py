import requests
import json

url = "http://127.0.0.1:9999/api/admin/verify-user"
payload = {
    "user_id": 6,
    "status": 1
}
headers = {
    "Content-Type": "application/json"
}

try:
    print(f"Sending POST to {url} with payload {payload}...")
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {str(e)}")
