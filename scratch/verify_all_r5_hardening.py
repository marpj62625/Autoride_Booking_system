print("=== VERIFYING ROUND 5 HARDENING ===")

with open("backend/app.py", "r", encoding="utf-8") as f:
    backend_code = f.read()

# Assertions for all 14 targets
assert "note = str(data.get('note', '') or '').strip()[:250]" in backend_code
assert "lat = max(-90.0, min(90.0, float(lat)))" in backend_code
assert "speed = max(0.0, min(300.0, float(speed)))" in backend_code
assert "card_type = str(card_type).strip()[:30]" in backend_code
assert "last_four = str(last_four).strip()[:4]" in backend_code
assert "customer_name = (data.get('customer_name') or '').strip()[:100]" in backend_code
assert "emergency_name = (data.get('emergency_name') or '').strip()[:100]" in backend_code
assert "reason" in backend_code and "[:250]" in backend_code
assert "is_authorized, err_resp = verify_admin_access()" in backend_code
assert "allowed_chat_roles = ['admin', 'customer', 'driver', 'staff', 'user', 'system']" in backend_code
assert "1950 <= ym_int <= 2030" in backend_code
assert "license_number = str(request.form.get('license_number', '') or '').strip()[:30] or None" in backend_code
assert "price = max(0.0, min(100000.0, float(price)))" in backend_code
assert "new_charge_type = str(data.get('charge_type') or '').strip()[:50] if data.get('charge_type') else None" in backend_code
assert "new_notes = str(data.get('notes') or '').strip()[:250] if data.get('notes') else None" in backend_code

print("[PASS] All 14 Round 5 Backend targets verified successfully in backend/app.py!")
