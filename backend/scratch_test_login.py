import requests

def test_login():
    url = "http://127.0.0.1:9999/api/admin/login"
    payload = {
        "email": "superadmin@autoride.com",
        "password": "admin12345"
    }
    try:
        response = requests.post(url, json=payload)
        print(f"STATUS: {response.status_code}")
        print(f"RESPONSE: {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_login()
