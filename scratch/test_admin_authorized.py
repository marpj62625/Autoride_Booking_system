import sys
sys.path.insert(0, 'backend')
from app import app
from database import get_cursor

client = app.test_client()

with app.app_context():
    cur = get_cursor()
    cur.execute("SELECT id, role, email FROM users WHERE role IN ('admin', 'super_admin') LIMIT 1")
    admin = cur.fetchone()

print(f"Found admin account in DB: ID={admin['id']}, Role={admin['role']}, Email={admin['email']}")

# Test 1: Admin authorized settings check
res = client.post('/api/admin/settings', json={
    "admin_id": admin['id'],
    "settings": [{"key": "test_system_health", "value": "healthy"}]
})
print("Admin Settings Update Status:", res.status_code, res.get_json())
assert res.status_code == 200

# Test 2: Admin authorized password reset
res2 = client.post(f"/api/admin/users/{admin['id']}/reset-password", json={
    "admin_id": admin['id'],
    "new_password": "short" # validation check
})
print("Password length validation status:", res2.status_code, res2.get_json())
assert res2.status_code == 400 and "Password must be at least 8 characters" in str(res2.get_json())

print("ALL AUTHORIZED ADMIN INTEGRATION CHECKS PASSED!")
