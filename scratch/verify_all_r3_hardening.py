import sys

print("=== VERIFYING ROUND 3 HARDENING ===")

# 1. Customer JS
with open('AutorideSystem/customer_mobile/www/js/app.js', 'r', encoding='utf-8') as f:
    cjs = f.read()

assert '<input type="number" id="inspMileage" min="0" max="999999" placeholder="e.g. 12500">' in cjs
print("[CUSTOMER JS PASS]: inspMileage bounded with min=0 max=999999")

# 2. Admin HTML
with open('AutorideSystem/admin_app/index.html', 'r', encoding='utf-8') as f:
    adm = f.read()

admin_checks = [
    'id="driverWageInput" maxlength="50"',
    'id="driverSearchInput" maxlength="50"',
    'id="fleetVehicleRateInput" value="${curRate}" step="50" min="0" max="50000"',
    'id="refundRefInput_${b.id}" maxlength="50"',
    'id="extRfAmt_${extensionId}" type="number" step="0.01" min="0" max="500000"',
    'id="extRfRef_${extensionId}" type="text" maxlength="50"',
    'id="umEditName" type="text" maxlength="50"',
    'id="umEditPhone" type="text" maxlength="11"',
    'id="umLoyaltyInput" type="number" min="0" max="100000"',
    'id="umNewPass" type="password" maxlength="64"',
    'id="editNote_${u.id}" maxlength="200"',
    'id="umFreezeReason" type="text" maxlength="200"',
    'id="chatSearchInput" maxlength="50"',
    'id="acUserSearchInput" maxlength="50"',
    'id="acInput" maxlength="500"',
    'id="manualSmtpEmail" type="email" maxlength="60"',
    'id="manualSmtpPass" type="password" maxlength="64"',
    'id="testEmailRecipient" type="email" maxlength="60"',
    'data-key="${s.key}" maxlength="255"',
    'data-key="${s.key}" maxlength="500" value="${val}" placeholder="${placeholder}"',
    '<textarea data-key="${s.key}" maxlength="5000"',
    'data-key="${s.key}" maxlength="500" value="${val}" style='
]

for c in admin_checks:
    assert c in adm, f"Admin check failed: {c}"
print(f"[ADMIN HTML PASS]: All {len(admin_checks)} admin bounds verified")

# 3. Backend app.py
with open('AutorideSystem/backend/app.py', 'r', encoding='utf-8') as f:
    bke = f.read()

backend_checks = [
    "limit = max(1, min(int(request.args.get('limit', 100) or 100), 500))",
    "points_redeemed = max(0, int(data.get('points_redeemed', 0) or 0))",
    'd1 = datetime.strptime(str(new_start)[:10], "%Y-%m-%d")',
    "page_size not in [10, 25, 50, 100]",
    "limit = max(1, min(int(request.args.get('limit', 10) or 10), 50))",
    "limit = max(1, min(int(request.args.get('limit', 50) or 50), 100))",
    "new_amount_val = max(0.0, min(100000.0, float(new_amount)))",
    "first_name = (data.get('first_name', '') or '').strip()[:30]",
    "points_val = max(0, min(100000, int(points)))",
    "len(new_password) < 8 or len(new_password) > 64",
    "reason = (data.get('reason', '') or '').strip()[:200]",
    "note = (data.get('note') or '').strip()[:200]"
]

for b in backend_checks:
    assert b in bke, f"Backend check failed: {b}"
print(f"[BACKEND PASS]: All {len(backend_checks)} backend crash defenses and bounds verified")

print("\nALL ROUND 3 CHECKS PASSED PERFECTLY!")
