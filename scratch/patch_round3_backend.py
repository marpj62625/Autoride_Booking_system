import sys

BACKEND_APP = 'AutorideSystem/backend/app.py'

with open(BACKEND_APP, 'r', encoding='utf-8') as f:
    content = f.read()

patches = [
    # 1. get_vehicle_gps_history
    (
        "limit = min(int(request.args.get('limit', 100)), 500)",
        """try:
        limit = max(1, min(int(request.args.get('limit', 100) or 100), 500))
    except (ValueError, TypeError):
        limit = 100"""
    ),
    # 2. book points_redeemed
    (
        "            # Validate and cap loyalty points\n            points_redeemed = max(0, int(data.get('points_redeemed', 0) or 0))",
        """            # Validate and cap loyalty points
            try:
                points_redeemed = max(0, int(data.get('points_redeemed', 0) or 0))
            except (ValueError, TypeError):
                points_redeemed = 0"""
    ),
    # 3. reschedule_booking strptime
    (
        """        # Calculate new days
        from datetime import datetime
        d1 = datetime.strptime(new_start, "%Y-%m-%d")
        d2 = datetime.strptime(new_end, "%Y-%m-%d")
        new_days = (d2 - d1).days + 1""",
        """        # Calculate new days
        from datetime import datetime
        try:
            d1 = datetime.strptime(str(new_start)[:10], "%Y-%m-%d")
            d2 = datetime.strptime(str(new_end)[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        new_days = (d2 - d1).days + 1"""
    ),
    # 4. get_cancelled_bookings pagination
    (
        """        # Get pagination parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 25))
        sort_by = request.args.get('sort_by', 'cancellation_date_desc')
        
        # Validate page_size
        if page_size not in [10, 25, 50, 100]:
            page_size = 25""",
        """        # Get pagination parameters
        try:
            page = max(1, int(request.args.get('page', 1) or 1))
        except (ValueError, TypeError):
            page = 1
        try:
            page_size = int(request.args.get('page_size', 25) or 25)
        except (ValueError, TypeError):
            page_size = 25
        if page_size not in [10, 25, 50, 100]:
            page_size = 25
        sort_by = request.args.get('sort_by', 'cancellation_date_desc')"""
    ),
    # 5. users_search limit & q
    (
        """    q = (request.args.get('q') or '').strip()
    limit = min(int(request.args.get('limit', 10)), 50)""",
        """    q = (request.args.get('q') or '').strip()[:50]
    try:
        limit = max(1, min(int(request.args.get('limit', 10) or 10), 50))
    except (ValueError, TypeError):
        limit = 10"""
    ),
    # 6. chat_messages limit
    (
        """    user_id  = request.args.get('user_id')
    admin_id = request.args.get('admin_id')
    limit    = int(request.args.get('limit', 50))""",
        """    user_id  = request.args.get('user_id')
    admin_id = request.args.get('admin_id')
    try:
        limit = max(1, min(int(request.args.get('limit', 50) or 50), 100))
    except (ValueError, TypeError):
        limit = 50"""
    ),
    # 7. edit_penalty amount
    (
        """    if new_amount is None:
        return jsonify({'error': 'Amount is required'}), 400

    try:
        cur = get_cursor()
        cur.execute("SELECT booking_id, amount, charge_type FROM booking_penalties WHERE id = %s", (p_id,))
        p_row = cur.fetchone()
        if not p_row:
            return jsonify({'error': 'Penalty not found'}), 404
        booking_id = p_row['booking_id']

        update_fields = ["amount = %s"]
        params = [float(new_amount)]""",
        """    if new_amount is None:
        return jsonify({'error': 'Amount is required'}), 400

    try:
        new_amount_val = max(0.0, min(100000.0, float(new_amount)))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid penalty amount'}), 400

    try:
        cur = get_cursor()
        cur.execute("SELECT booking_id, amount, charge_type FROM booking_penalties WHERE id = %s", (p_id,))
        p_row = cur.fetchone()
        if not p_row:
            return jsonify({'error': 'Penalty not found'}), 404
        booking_id = p_row['booking_id']

        update_fields = ["amount = %s"]
        params = [new_amount_val]"""
    ),
    # 8. admin_edit_user
    (
        """def admin_edit_user(user_id):
    \"\"\"Edit user basic info.\"\"\"
    data = request.get_json(silent=True) or {}
    first_name = data.get('first_name', '').strip()
    middle_name = data.get('middle_name', '').strip()
    last_name = data.get('last_name', '').strip()
    phone = data.get('phone', '').strip()
    if not first_name or not last_name:
        return jsonify({"error": "First name and last name are required"}), 400""",
        """def admin_edit_user(user_id):
    \"\"\"Edit user basic info.\"\"\"
    is_authorized, err_resp = verify_admin_access()
    if not is_authorized:
        return err_resp
    data = request.get_json(silent=True) or {}
    first_name = (data.get('first_name', '') or '').strip()[:30]
    middle_name = (data.get('middle_name', '') or '').strip()[:30]
    last_name = (data.get('last_name', '') or '').strip()[:30]
    phone = (data.get('phone', '') or '').strip()[:11]
    if not first_name or not last_name:
        return jsonify({"error": "First name and last name are required"}), 400"""
    ),
    # 9. admin_set_loyalty
    (
        """def admin_set_loyalty(user_id):
    \"\"\"Set loyalty points for a user.\"\"\"
    data = request.get_json(silent=True) or {}
    points = data.get('points')
    if points is None or not str(points).lstrip('-').isdigit():
        return jsonify({"error": "Valid points value required"}), 400
    try:
        cur = get_cursor()
        cur.execute("UPDATE users SET loyalty_points = %s WHERE id = %s", (int(points), user_id))""",
        """def admin_set_loyalty(user_id):
    \"\"\"Set loyalty points for a user.\"\"\"
    is_authorized, err_resp = verify_admin_access()
    if not is_authorized:
        return err_resp
    data = request.get_json(silent=True) or {}
    points = data.get('points')
    if points is None:
        return jsonify({"error": "Valid points value required"}), 400
    try:
        points_val = max(0, min(100000, int(points)))
    except (ValueError, TypeError):
        return jsonify({"error": "Valid points value required"}), 400
    try:
        cur = get_cursor()
        cur.execute("UPDATE users SET loyalty_points = %s WHERE id = %s", (points_val, user_id))"""
    ),
    # 10. admin_reset_password
    (
        """    data = request.get_json(silent=True) or {}
    new_password = data.get('new_password', '').strip()
    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400""",
        """    data = request.get_json(silent=True) or {}
    new_password = (data.get('new_password', '') or '').strip()
    if len(new_password) < 8 or len(new_password) > 64:
        return jsonify({"error": "Password must be between 8 and 64 characters"}), 400"""
    ),
    # 11. admin_freeze_user
    (
        """    data = request.get_json(silent=True) or {}
    freeze = data.get('freeze', True)
    reason = data.get('reason', '')""",
        """    data = request.get_json(silent=True) or {}
    freeze = data.get('freeze', True)
    reason = (data.get('reason', '') or '').strip()[:200]"""
    ),
    # 12. admin_edit_user_violations
    (
        """def admin_edit_user_violations(user_id):
    \"\"\"
    Admin manually updates a user's account standing:
    - violation_strikes (int)
    - booking_suspension_until (ISO string, datetime, or null)
    - violation_permanently_restricted (bool)
    - violation_commitment_fee_required (bool)
    - admin_id (int)
    - note (str)
    \"\"\"
    data = request.get_json(silent=True) or {}
    strikes = data.get('violation_strikes')
    susp_until = data.get('booking_suspension_until')
    perm = data.get('violation_permanently_restricted')
    fee_req = data.get('violation_commitment_fee_required')
    note = (data.get('note') or '').strip()""",
        """def admin_edit_user_violations(user_id):
    \"\"\"
    Admin manually updates a user's account standing:
    - violation_strikes (int)
    - booking_suspension_until (ISO string, datetime, or null)
    - violation_permanently_restricted (bool)
    - violation_commitment_fee_required (bool)
    - admin_id (int)
    - note (str)
    \"\"\"
    is_authorized, err_resp = verify_admin_access()
    if not is_authorized:
        return err_resp
    data = request.get_json(silent=True) or {}
    strikes = data.get('violation_strikes')
    susp_until = data.get('booking_suspension_until')
    perm = data.get('violation_permanently_restricted')
    fee_req = data.get('violation_commitment_fee_required')
    note = (data.get('note') or '').strip()[:200]"""
    ),
    # 13. activity_logs
    (
        """        filter_type = (request.args.get('filter') or request.args.get('action') or '').strip().lower()
        search_query = (request.args.get('q') or request.args.get('search') or '').strip().lower()""",
        """        filter_type = (request.args.get('filter') or request.args.get('action') or '').strip().lower()[:50]
        search_query = (request.args.get('q') or request.args.get('search') or '').strip().lower()[:50]"""
    ),
    # 14. activity_logs page/limit safe parse
    (
        """        if page:
            page = int(page)
            limit = int(limit) if limit else 50
            offset = (page - 1) * limit""",
        """        if page:
            try:
                page = max(1, int(page))
            except (ValueError, TypeError):
                page = 1
            try:
                limit = max(1, min(100, int(limit))) if limit else 50
            except (ValueError, TypeError):
                limit = 50
            offset = (page - 1) * limit"""
    )
]

all_ok = True
for idx, (old, new) in enumerate(patches):
    cnt = content.count(old)
    if cnt != 1:
        print(f"FAILED: item {idx+1} found {cnt} occurrences: {old[:50]}...")
        all_ok = False
    else:
        print(f"OK: item {idx+1}")

if not all_ok:
    print("\nAborting: Not all items matched uniquely.")
    sys.exit(1)

for old, new in patches:
    content = content.replace(old, new, 1)

with open(BACKEND_APP, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nSUCCESS: All {len(patches)} Round 3 backend targets patched into backend/app.py")
