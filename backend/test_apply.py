import requests
import os

# Create a dummy license image
dummy_file_path = "test_license_img.jpg"
with open(dummy_file_path, "wb") as f:
    f.write(b"fake image content")

url = "http://127.0.0.1:5000/driver/apply"
data = {
    "user_id": 9999,
    "full_name": "Test Apply Driver",
    "license_number": "LIC-999-XXXX",
    "contact_info": "0912-345-6789"
}

files = {
    "license_document": open(dummy_file_path, "rb")
}

try:
    print("Sending POST to /driver/apply...")
    response = requests.post(url, data=data, files=files)
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", str(e))
finally:
    files["license_document"].close()
