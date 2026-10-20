print("=== VERIFYING ROUND 7 HARDENING ===")

with open("backend/app.py", "r", encoding="utf-8") as f:
    backend_code = f.read()

# Assertions for Round 7 targets
assert "if len(password) > 128:" in backend_code
assert "pickup_dt = _dtm.datetime.now()" in backend_code
assert "pickup_dt = cancel_dt" in backend_code
assert "Invalid requester_id" in backend_code
assert "limit = max(1, min(100, int(request.args.get('limit', 50) or 50)))" in backend_code
assert "viewer_type not in ['admin', 'user', 'customer', 'driver', 'staff', 'system']:" in backend_code
assert "Invalid viewer_id format" in backend_code
assert "vehicle_id = int(vehicle_id) if vehicle_id else None" in backend_code
assert "New password must be between 6 and 64 characters." in backend_code

print("[PASS] All Round 7 Backend targets verified successfully in backend/app.py!")
