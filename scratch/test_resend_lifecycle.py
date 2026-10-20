import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
from app import app, get_cursor

with app.app_context():
    client = app.test_client()
    res = client.post('/api/auth/resend-otp', json={"email": "rnaa10061@gmail.com"})
    print("resend-otp status:", res.status_code, res.get_json())
    assert res.status_code == 200

    cur = get_cursor()
    cur.execute("SELECT otp FROM email_verification_otps WHERE email = 'rnaa10061@gmail.com'")
    row = cur.fetchone()
    print("New OTP in DB:", row['otp'])
    assert len(row['otp']) == 6

    # Verify with this new OTP
    res_verify = client.post('/api/auth/verify-email', json={"email": "rnaa10061@gmail.com", "otp": row['otp']})
    print("verify status:", res_verify.status_code, res_verify.get_json())
    assert res_verify.status_code == 200
    print("[PASS] Resend and verify full flow tested and confirmed!")
