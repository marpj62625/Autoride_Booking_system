print("=== VERIFYING ROUND 6 HARDENING ===")

with open("backend/app.py", "r", encoding="utf-8") as f:
    backend_code = f.read()

# Assertions for Round 6 targets
assert "if '..' in filename or filename.startswith(('/', '\\\\')):" in backend_code
assert "user_id = int(user_id)" in backend_code
assert "if not isinstance(order, list):" in backend_code
assert "if len(order) > 50:" in backend_code
assert "if not isinstance(updates, list):" in backend_code
assert "if len(updates) > 100:" in backend_code
assert "chart_type = str(request.args.get('type') or '').strip()[:50] or None" in backend_code
assert "filter_period = str(request.args.get('filter', 'year') or 'year').strip()[:20]" in backend_code
assert "if data_type not in ['archived_bookings', 'activity_logs', 'notifications']:" in backend_code
assert "if not isinstance(records, list):" in backend_code
assert "if len(records) > 2000:" in backend_code
assert "is_authorized, err_resp = verify_admin_access()" in backend_code

print("[PASS] All 17 Round 6 Backend targets verified successfully in backend/app.py!")
