import sys

BACKEND_PATH = "backend/app.py"

with open(BACKEND_PATH, "r", encoding="utf-8") as f:
    content = f.read()

orig_len = len(content)

# Target 1: login Bcrypt DoS defense (~Line 2793)
p1_old = """    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not email or not password:
        return jsonify({"error": "Missing credentials"}), 400"""

p1_new = """    email = (data.get('email') or '').strip().lower()[:100]
    password = (data.get('password') or '').strip()

    if not email or not password:
        return jsonify({"error": "Missing credentials"}), 400

    if len(password) > 128:
        return jsonify({"error": "Password exceeds maximum length"}), 400"""

assert p1_old in content, "Target 1 (login) pattern not found"
content = content.replace(p1_old, p1_new, 1)

# Target 2: user_bookings user_id validation (~Line 6140)
p2_old = """def user_bookings():

    user_id = request.args.get('user_id')

    if not user_id:

        return jsonify({"error": "user_id is required"}), 400

        

    try:"""

p2_new = """def user_bookings():

    user_id = request.args.get('user_id')

    if not user_id:

        return jsonify({"error": "user_id is required"}), 400

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid user_id"}), 400

    try:"""

assert p2_old in content, "Target 2 (user_bookings) pattern not found"
content = content.replace(p2_old, p2_new, 1)

# Target 3: strptime crash defense in cancel penalty 1 (~Line 8684)
p3_old = """            else:
                pickup_dt = _dtm.datetime.strptime(str(start_raw)[:10], '%Y-%m-%d').replace(hour=6)"""

p3_new = """            else:
                try:
                    pickup_dt = _dtm.datetime.strptime(str(start_raw)[:10], '%Y-%m-%d').replace(hour=6)
                except Exception:
                    pickup_dt = _dtm.datetime.now()"""

assert p3_old in content, "Target 3 (strptime 1) pattern not found"
content = content.replace(p3_old, p3_new, 1)

# Target 4: strptime crash defense in cancel penalty 2 (~Line 8902)
p4_old = """        else:
            pickup_dt = _dtm.datetime.strptime(str(start_raw)[:10], '%Y-%m-%d').replace(hour=6)"""

p4_new = """        else:
            try:
                pickup_dt = _dtm.datetime.strptime(str(start_raw)[:10], '%Y-%m-%d').replace(hour=6)
            except Exception:
                pickup_dt = cancel_dt"""

assert p4_old in content, "Target 4 (strptime 2) pattern not found"
content = content.replace(p4_old, p4_new, 1)

# Target 5: admin_login Bcrypt DoS defense (~Line 12327)
p5_old = """    email = data.get('email')

    password = data.get('password')

    

    try:"""

p5_new = """    email = str(data.get('email') or '').strip().lower()[:100]

    password = str(data.get('password') or '').strip()

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    if len(password) > 128:
        return jsonify({"error": "Password exceeds maximum length"}), 400

    try:"""

assert p5_old in content, "Target 5 (admin_login) pattern not found"
content = content.replace(p5_old, p5_new, 1)

# Target 6: list_admins requester_id cast (~Line 12393)
p6_old = """def list_admins():

    requester_id = request.args.get('requester_id')

    try:"""

p6_new = """def list_admins():

    requester_id = request.args.get('requester_id')
    try:
        requester_id = int(requester_id) if requester_id else None
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid requester_id"}), 400

    try:"""

assert p6_old in content, "Target 6 (list_admins) pattern not found"
content = content.replace(p6_old, p6_new, 1)

# Target 7: delete_admin requester_id cast (~Line 12529)
p7_old = """def delete_admin(user_id):

    requester_id = request.args.get('requester_id')

    try:"""

p7_new = """def delete_admin(user_id):

    requester_id = request.args.get('requester_id')
    try:
        requester_id = int(requester_id) if requester_id else None
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid requester_id"}), 400

    try:"""

assert p7_old in content, "Target 7 (delete_admin) pattern not found"
content = content.replace(p7_old, p7_new, 1)

# Target 8: update_super_admin_profile password bounds (~Line 12590)
p8_old = """    current_password = str(data.get('current_password', '')).strip()
    new_email = str(data.get('email', '')).strip().lower()
    new_password = str(data.get('new_password', '')).strip()"""

p8_new = """    current_password = str(data.get('current_password', '')).strip()[:128]
    new_email = str(data.get('email', '')).strip().lower()[:100]
    new_password = str(data.get('new_password', '')).strip()[:128]
    if new_password and (len(new_password) < 6 or len(new_password) > 64):
        return jsonify({"error": "New password must be between 6 and 64 characters."}), 400"""

assert p8_old in content, "Target 8 (update_super_admin_profile) pattern not found"
content = content.replace(p8_old, p8_new, 1)

# Target 9: get_activity_logs safe page/limit (~Line 14073)
p9_old = """        page = request.args.get('page')
        limit = request.args.get('limit')
        filter_type = (request.args.get('filter') or request.args.get('action') or '').strip().lower()[:50]"""

p9_new = """        try:
            page = max(1, int(request.args.get('page', 1) or 1))
        except (ValueError, TypeError):
            page = 1
        try:
            limit = max(1, min(100, int(request.args.get('limit', 50) or 50)))
        except (ValueError, TypeError):
            limit = 50
        filter_type = (request.args.get('filter') or request.args.get('action') or '').strip().lower()[:50]"""

assert p9_old in content, "Target 9 (get_activity_logs) pattern not found"
content = content.replace(p9_old, p9_new, 1)

# Target 10: get_vehicle_location_for_customer user_id cast (~Line 14206)
p10_old = """    user_id = request.args.get('user_id')

    if not user_id:

        return jsonify({"error": "user_id is required"}), 400



    try:"""

p10_new = """    user_id = request.args.get('user_id')

    if not user_id:

        return jsonify({"error": "user_id is required"}), 400

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid user_id"}), 400

    try:"""

assert p10_old in content, "Target 10 (get_vehicle_location_for_customer) pattern not found"
content = content.replace(p10_old, p10_new, 1)

# Target 11: get_vehicle_units bounds (~Line 14340)
p11_old = """    brand = request.args.get('brand', '')
    model = request.args.get('model', '')
    color = request.args.get('color', '')
    user_id = request.args.get('user_id', '')
    if not brand or not model:
        return jsonify({'error': 'brand and model are required'}), 400"""

p11_new = """    brand = str(request.args.get('brand', '')).strip()[:50]
    model = str(request.args.get('model', '')).strip()[:50]
    color = str(request.args.get('color', '')).strip()[:50]
    user_id = request.args.get('user_id', '')
    if user_id:
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            user_id = None
    if not brand or not model:
        return jsonify({'error': 'brand and model are required'}), 400"""

assert p11_old in content, "Target 11 (get_vehicle_units) pattern not found"
content = content.replace(p11_old, p11_new, 1)

# Target 12: get_license_details user_id cast (~Line 14655)
p12_old = """        if not user_id or user_id.strip() == '':
            return jsonify({
                'error': 'user_id required or empty',
                'debug': debug_info
            }), 400"""

p12_new = """        if not user_id or user_id.strip() == '':
            return jsonify({
                'error': 'user_id required or empty',
                'debug': debug_info
            }), 400
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid user_id'}), 400"""

assert p12_old in content, "Target 12 (get_license_details) pattern not found"
content = content.replace(p12_old, p12_new, 1)

# Target 13: chat_messages safe user_id & admin_id (~Line 16296)
p13_old = """    if not user_id or not admin_id:
        return jsonify({'error': 'user_id and admin_id required'}), 400
    try:
        cur = get_cursor()"""

p13_new = """    if not user_id or not admin_id:
        return jsonify({'error': 'user_id and admin_id required'}), 400
    try:
        user_id = int(user_id)
        admin_id = int(admin_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid user_id or admin_id format'}), 400
    try:
        cur = get_cursor()"""

assert p13_old in content, "Target 13 (chat_messages) pattern not found"
content = content.replace(p13_old, p13_new, 1)

# Target 14: chat threads viewer_type whitelist & viewer_id cast (~Line 16426)
p14_old = """    viewer_type = request.args.get('viewer_type')  # 'admin' or 'user'
    viewer_id   = request.args.get('viewer_id')
    if not viewer_type or not viewer_id:
        return jsonify({'error': 'viewer_type and viewer_id required'}), 400
    try:
        cur = get_cursor()"""

p14_new = """    viewer_type = str(request.args.get('viewer_type') or '').strip().lower()
    viewer_id   = request.args.get('viewer_id')
    if not viewer_type or not viewer_id:
        return jsonify({'error': 'viewer_type and viewer_id required'}), 400
    if viewer_type not in ['admin', 'user', 'customer', 'driver', 'staff', 'system']:
        return jsonify({'error': 'Invalid viewer_type'}), 400
    try:
        viewer_id = int(viewer_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid viewer_id format'}), 400
    try:
        cur = get_cursor()"""

assert p14_old in content, "Target 14 (chat threads) pattern not found"
content = content.replace(p14_old, p14_new, 1)

# Target 15: get_expenses admin auth & filters (~Line 17007)
p15_old = """def get_expenses():
    \"\"\"Retrieve filtered list of expenses.\"\"\"
    admin_id = request.args.get('admin_id')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    vehicle_id = request.args.get('vehicle_id')

    try:"""

p15_new = """def get_expenses():
    \"\"\"Retrieve filtered list of expenses.\"\"\"
    is_authorized, err_resp = verify_admin_access()
    if not is_authorized:
        return err_resp

    admin_id = request.args.get('admin_id')
    try:
        admin_id = int(admin_id) if admin_id else None
    except (ValueError, TypeError):
        admin_id = None

    vehicle_id = request.args.get('vehicle_id')
    try:
        vehicle_id = int(vehicle_id) if vehicle_id else None
    except (ValueError, TypeError):
        vehicle_id = None

    date_from = str(request.args.get('date_from') or '').strip()[:10] or None
    date_to = str(request.args.get('date_to') or '').strip()[:10] or None

    try:"""

assert p15_old in content, "Target 15 (get_expenses) pattern not found"
content = content.replace(p15_old, p15_new, 1)

with open(BACKEND_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully applied all 15 Round 7 patches! Original: {orig_len} chars, New: {len(content)} chars.")
