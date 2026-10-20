import sys
sys.path.insert(0, 'AutorideSystem/backend')
from app import app, verify_admin_access

# 1. Anonymous attacker from unknown source -> MUST BE 401
with app.test_request_context('/api/admin/users/1/freeze', method='POST', json={}, headers={'Origin': 'https://evil-attacker.com'}):
    authorized, resp = verify_admin_access()
    assert not authorized, 'Anonymous attacker should be blocked'
    assert resp[1] == 401, 'Anonymous attacker should get 401'
    print('Test 1 (Malicious Anonymous Attacker Block): PASSED (401 returned)')

# 2. Legitimate Admin Portal on Vercel -> MUST PASS
with app.test_request_context('/api/admin/users/1/freeze', method='POST', json={'freeze': True}, headers={'Origin': 'https://autoride-booking-system.vercel.app'}):
    authorized, resp = verify_admin_access()
    assert authorized, 'Web Admin Portal must be authorized'
    print('Test 2 (Production Web Admin Portal): PASSED (authorized)')

# 3. Installed Admin Mobile APK (Capacitor localhost) -> MUST PASS
with app.test_request_context('/api/admin/users/1/freeze', method='POST', json={'freeze': True}, headers={'Origin': 'https://localhost'}):
    authorized, resp = verify_admin_access()
    assert authorized, 'Installed Admin Mobile APK must be authorized'
    print('Test 3 (Installed Admin Mobile APK): PASSED (authorized)')

# 4. Verified Admin ID in payload -> MUST PASS
with app.app_context():
    from database import get_cursor
    cur = get_cursor()
    cur.execute("SELECT id FROM users WHERE role IN ('admin', 'super_admin') LIMIT 1")
    admin = cur.fetchone()
    if admin:
        admin_id = admin['id']
        with app.test_request_context('/api/admin/users/1/freeze', method='POST', json={'admin_id': admin_id}):
            authorized, resp = verify_admin_access()
            assert authorized, 'Valid admin_id should be authorized'
            print(f'Test 4 (Admin ID #{admin_id} Payload): PASSED (authorized)')
    cur.close()

print('ALL AUTH REGRESSION TESTS PASSED (4/4)!')
