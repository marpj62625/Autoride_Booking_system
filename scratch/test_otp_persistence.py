import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
from app import app, get_cursor, commit_db, save_email_otp, verify_email_otp

with app.app_context():
    print("Testing save_email_otp and verify_email_otp...")
    test_email = "autotest_user@gmail.com"
    test_otp = "987654"
    save_email_otp(test_email, test_otp)
    
    assert verify_email_otp(test_email, "000000") == False, "Wrong OTP should fail"
    assert verify_email_otp(test_email, test_otp) == True, "Correct OTP should succeed"
    assert verify_email_otp(test_email, test_otp) == False, "Reused OTP should fail"
    print("[PASS] Unit tests for save_email_otp and verify_email_otp passed!")

    # Test Flask test client for verify-email endpoint
    client = app.test_client()
    
    # Save code for rnaa10061@gmail.com
    save_email_otp("rnaa10061@gmail.com", "353963")
    res = client.post('/api/auth/verify-email', json={
        "email": "rnaa10061@gmail.com",
        "otp": "353963"
    })
    print("verify-email response for rnaa10061@gmail.com:", res.status_code, res.get_json())
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.get_json()}"

    cur = get_cursor()
    cur.execute("SELECT id, email, is_email_verified FROM users WHERE email = 'rnaa10061@gmail.com'")
    user = cur.fetchone()
    print("Updated DB user record:", user)
    assert user['is_email_verified'] == True, "User is_email_verified should now be True!"
    print("[ALL OTP VERIFICATION TESTS PASSED SUCCESSFULLY!]")
