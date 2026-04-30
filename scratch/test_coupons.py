import requests
import json

BASE_URL = "http://localhost:9999"

def test_coupons():
    print("--- Testing Promo Code System ---")
    
    # 1. Test valid coupon
    print("Testing valid coupon 'WELCOME10'...")
    res = requests.post(f"{BASE_URL}/api/validate-coupon", json={"code": "WELCOME10"})
    data = res.json()
    if res.ok and data.get('valid'):
        print(f"SUCCESS: 'WELCOME10' is valid. Discount: {data['discount_percent']}%")
    else:
        print(f"FAILURE: 'WELCOME10' failed: {data}")

    # 2. Test invalid coupon
    print("Testing invalid coupon 'FAKECODE'...")
    res = requests.post(f"{BASE_URL}/api/validate-coupon", json={"code": "FAKECODE"})
    data = res.json()
    if not data.get('valid'):
        print(f"SUCCESS: 'FAKECODE' was correctly rejected: {data.get('message')}")
    else:
        print(f"FAILURE: 'FAKECODE' was accepted!")

if __name__ == "__main__":
    test_coupons()
