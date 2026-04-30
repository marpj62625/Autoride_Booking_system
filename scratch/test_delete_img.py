import requests

API_BASE = "http://127.0.0.1:9999"

def test_delete_image():
    # 1. Get a vehicle to find an image ID
    res = requests.get(f"{API_BASE}/vehicles")
    vehicles = res.json()
    
    if not vehicles:
        print("No vehicles found to test with.")
        return

    # Find a vehicle with images
    target_img_id = None
    for v in vehicles:
        if v.get('gallery_details'):
            target_img_id = v['gallery_details'][0]['id']
            print(f"Testing deletion of image ID: {target_img_id} for vehicle: {v['name']}")
            break
    
    if not target_img_id:
        print("No images found to test deletion.")
        return

    # 2. Try to delete
    res = requests.delete(f"{API_BASE}/api/vehicles/images/{target_img_id}")
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.json()}")

if __name__ == "__main__":
    test_delete_image()
