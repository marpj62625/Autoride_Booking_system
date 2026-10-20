import sys
import os

sys.path.insert(0, 'backend')
from app import app

client = app.test_client()

print("=" * 80)
print("TESTING SECURITY VULNERABILITIES & EDGE CASES")
print("=" * 80)

def test_endpoint(name, method, url, data=None, headers=None, expected_status=[200]):
    fn = getattr(client, method.lower())
    kwargs = {}
    if data is not None:
        if isinstance(data, dict):
            kwargs['json'] = data
        else:
            kwargs['data'] = data
    if headers:
        kwargs['headers'] = headers
    res = fn(url, **kwargs)
    status = res.status_code
    passed = status in expected_status
    print(f"[{'PASS' if passed else 'FAIL'}] {name}")
    print(f"  Method: {method} {url}")
    print(f"  Status: {status} (Expected: {expected_status})")
    try:
        body = res.get_json()
        print(f"  Response: {str(body)[:120]}")
    except Exception:
        print(f"  Response (text): {res.data[:120]}")
    print("-" * 60)
    return passed

# Test 1: Past Bookings Route (Must be 200, not 404)
test_endpoint(
    "1. Past Bookings Route Existence",
    "GET",
    "/api/bookings/past",
    expected_status=[200]
)

# Test 2: Unauthenticated Admin Settings Mutation (Should be 401/403, NOT 200)
test_endpoint(
    "2. Block Unauthenticated Settings Takeover",
    "POST",
    "/api/admin/settings",
    data={"settings": [{"key": "test_hack", "value": "hacked"}]},
    expected_status=[401, 403]
)

# Test 3: Unauthenticated Password Reset (Should be 401/403, NOT 200)
test_endpoint(
    "3. Block Unauthenticated User Password Reset",
    "POST",
    "/api/admin/users/1/reset-password",
    data={"new_password": "HackedPassword123"},
    expected_status=[401, 403]
)

# Test 4: Unauthenticated User Deletion (Should be 401/403, NOT 200)
test_endpoint(
    "4. Block Unauthenticated User Deletion",
    "DELETE",
    "/api/admin/users/999999",
    expected_status=[401, 403]
)

# Test 5: Vehicle Deletion Without Admin ID (Should be 401/403, NOT 200)
test_endpoint(
    "5. Block Anonymous Vehicle Deletion",
    "DELETE",
    "/api/vehicles/999999",
    expected_status=[401, 403]
)

# Test 6: Unauthenticated Booking Self-Approval (Should be 401/403, NOT 200/400)
test_endpoint(
    "6. Block Customer Booking Self-Approval",
    "PUT",
    "/api/bookings/1/approve",
    expected_status=[401, 403]
)

# Test 7: Unauthenticated Booking Completion (Should be 401/403, NOT 200)
test_endpoint(
    "7. Block Customer Premature Booking Completion",
    "PUT",
    "/api/bookings/1/complete",
    expected_status=[401, 403]
)
