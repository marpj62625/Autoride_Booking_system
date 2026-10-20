import os
import re

print("=== VERIFYING ROUND 2 HARDENING ===")

# 1. Admin App
with open('AutorideSystem/admin_app/index.html', 'r', encoding='utf-8') as f:
    admin_content = f.read()

admin_checks = [
    'id="quickTotalPrice" step="50" min="0" max="500000"',
    'id="quickAmountPaid" step="50" min="0" max="500000"',
    'id="addonPriceInput" min="0" max="10000"',
    'id="insurancePriceInput" min="0" max="20000"',
    'id="locationFeeInput" min="0" max="10000"',
    'id="vehicleSearch" type="text" maxlength="50"',
    'id="nlSubSearchInput" maxlength="60"',
    'id="chatCtrlAiGreeting" maxlength="500"',
    'id="chatCtrlAiFallback" maxlength="500"',
    'id="faqFormChipLabel" maxlength="40"',
    'id="faqFormCategory" maxlength="30"',
    'id="faqFormQuestion" maxlength="150"',
    'id="faqFormKeywords" maxlength="200"',
    'id="faqFormAnswer" maxlength="1000"',
    'id="settingsSearchInput" maxlength="60"',
    'id="addonNameInput" maxlength="50"',
    'id="addonDescInput" maxlength="250"',
    'id="insuranceNameInput" maxlength="50"',
    'id="insuranceDescInput" maxlength="250"',
    'id="locationNameInput" maxlength="60"',
    'id="locationProvinceInput" maxlength="40"',
    'id="locationMuniInput" maxlength="40"',
    'id="locationBrgyInput" maxlength="40"',
    'id="newInstructionInput" maxlength="150"',
    'id="newMobilePassword" type="password" maxlength="64"',
    'id="confirmMobilePassword" type="password" maxlength="64"',
    'id="pushNotifTitle" maxlength="80"',
    'id="pushNotifBody" maxlength="500"',
    'id="staffReqPermReason" maxlength="250"',
    'id="gpsConfigDeviceName" maxlength="50"',
    'id="gpsConfigToken" maxlength="50"',
    'id="gpsConfigServer" maxlength="50"'
]

admin_pass = True
for check in admin_checks:
    if check not in admin_content:
        print(f"[ADMIN FAIL]: Missing check: {check}")
        admin_pass = False

if admin_pass:
    print(f"[ADMIN PASS]: All {len(admin_checks)} admin bounds verified in admin_app/index.html")

# 2. Customer OTP
with open('AutorideSystem/customer_mobile/www/index.html', 'r', encoding='utf-8') as f:
    cust_html = f.read()

otp_pass = True
for i in range(6):
    tag = f'<input type="tel" inputmode="numeric" pattern="[0-9]*" maxlength="1" id="otp{i}"'
    if tag not in cust_html:
        print(f"[OTP FAIL]: Missing {tag}")
        otp_pass = False

if otp_pass:
    print("[OTP HTML PASS]: All 6 OTP inputs use type=tel, pattern, inputmode, and maxlength=1")

with open('AutorideSystem/customer_mobile/www/js/app.js', 'r', encoding='utf-8') as f:
    cust_js = f.read()

if "el.value = el.value.replace(/[^0-9]/g, '').slice(-1);" in cust_js:
    print("[OTP JS PASS]: otpNext properly sanitizes and restricts digits")
else:
    print("[OTP JS FAIL]: otpNext digit sanitation missing")

# 3. Backend app.py
with open('AutorideSystem/backend/app.py', 'r', encoding='utf-8') as f:
    backend_content = f.read()

backend_checks = [
    ("reject_non_image for license upload", 'reject_non_image(file, "Driver\'s license")'),
    ("verify_email 6-digit & email limit", 'len(otp) != 6 or not otp.isdigit()'),
    ("process_refund bounds", 'refund_amount_val > 1000000'),
    ("process_refund proof guard", "reject_non_image(f, 'Proof screenshot')"),
    ("mark_booking_paid fee cast", 'Invalid payment fee format'),
    ("user_change_password length", 'Password must be between 6 and 64 characters.'),
    ("change_admin_password bounds", 'Password must be between 6 and 64 characters'),
    ("create_admin bounds", 'Valid admin email is required (max 60 characters).'),
    ("update_admin bounds", 'Admin name cannot exceed 50 characters.'),
    ("create_addon validation", 'max(0.0, min(10000.0, float(price)))'),
    ("create_insurance validation", 'max(0.0, min(20000.0, float(price)))'),
    ("save_license_details image check", 'if not is_allowed_image(file):'),
    ("update_booking_quick_pricing safe casts", 'Invalid price or amount values')
]

backend_pass = True
for label, snippet in backend_checks:
    if snippet not in backend_content:
        print(f"[BACKEND FAIL]: {label} missing")
        backend_pass = False

if backend_pass:
    print(f"[BACKEND PASS]: All {len(backend_checks)} backend validation guards verified")

print("\nALL ROUND 2 CHECKS COMPLETED!")
