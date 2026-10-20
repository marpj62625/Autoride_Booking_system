import sys

BACKEND_PATH = "backend/app.py"

with open(BACKEND_PATH, "r", encoding="utf-8") as f:
    content = f.read()

orig_len = len(content)

# Target 1: admin_reset_user_violations (~Line 3520)
p1_old = """def admin_reset_user_violations(user_id):
    \"\"\"Reset a user's strikes and lift any suspension.\"\"\"
    data = request.get_json(silent=True) or {}
    note = data.get('note', '')
    admin_id = data.get('admin_id')"""

p1_new = """def admin_reset_user_violations(user_id):
    \"\"\"Reset a user's strikes and lift any suspension.\"\"\"
    is_authorized, err_resp = verify_admin_access()
    if not is_authorized:
        return err_resp
    data = request.get_json(silent=True) or {}
    note = str(data.get('note', '') or '').strip()[:250]
    admin_id = data.get('admin_id')
    try:
        admin_id = int(admin_id) if admin_id else None
    except (ValueError, TypeError):
        admin_id = None"""

assert p1_old in content, "Target 1 (admin_reset_user_violations) pattern not found"
content = content.replace(p1_old, p1_new, 1)

# Target 2: update_vehicle_location (~Line 4895)
p2_old = """    if lat is None or lng is None:
        return jsonify({"error": "Latitude and Longitude are required"}), 400

    try:
        cur = get_cursor()"""

p2_new = """    if lat is None or lng is None:
        return jsonify({"error": "Latitude and Longitude are required"}), 400

    try:
        lat = max(-90.0, min(90.0, float(lat)))
        lng = max(-180.0, min(180.0, float(lng)))
        speed = max(0.0, min(300.0, float(speed)))
        address = str(address).strip()[:255] if address else None
        gps_status = str(gps_status).strip()[:20]
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid GPS coordinate or speed values"}), 400

    try:
        cur = get_cursor()"""

assert p2_old in content, "Target 2 (update_vehicle_location) pattern not found"
content = content.replace(p2_old, p2_new, 1)

# Target 3: save_payment (~Line 6725)
p3_old = """    if not all([user_id, card_type, last_four, provider]):

        return jsonify({"error": "Missing payment details"}), 400

        

    try:"""

p3_new = """    if not all([user_id, card_type, last_four, provider]):

        return jsonify({"error": "Missing payment details"}), 400

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid user_id"}), 400

    card_type = str(card_type).strip()[:30]
    last_four = str(last_four).strip()[:4]
    provider = str(provider).strip()[:50]

    try:"""

assert p3_old in content, "Target 3 (save_payment) pattern not found"
content = content.replace(p3_old, p3_new, 1)

# Target 4: create_walkin_booking (~Line 7422)
p4_old = """        customer_name = (data.get('customer_name') or '').strip()
        customer_phone = (data.get('customer_phone') or '').strip()
        customer_address = (data.get('customer_address') or '').strip()
        emergency_name = (data.get('emergency_name') or '').strip()
        emergency_phone = (data.get('emergency_phone') or '').strip()
        emergency_rel = (data.get('emergency_rel') or '').strip()"""

p4_new = """        customer_name = (data.get('customer_name') or '').strip()[:100]
        customer_phone = (data.get('customer_phone') or '').strip()[:20]
        customer_address = (data.get('customer_address') or '').strip()[:250]
        emergency_name = (data.get('emergency_name') or '').strip()[:100]
        emergency_phone = (data.get('emergency_phone') or '').strip()[:20]
        emergency_rel = (data.get('emergency_rel') or '').strip()[:50]"""

assert p4_old in content, "Target 4 (create_walkin_booking) pattern not found"
content = content.replace(p4_old, p4_new, 1)

# Target 5: user_cancel_booking (~Line 8578)
p5_old = """        data = request.get_json(silent=True) or {}
        booking_id = data.get('booking_id')
        user_id    = data.get('user_id')
        reason     = data.get('reason', 'No reason provided')"""

p5_new = """        data = request.get_json(silent=True) or {}
        booking_id = data.get('booking_id')
        user_id    = data.get('user_id')
        reason     = str(data.get('reason', 'No reason provided') or 'No reason provided').strip()[:250]

        if not booking_id:
            return jsonify({"error": "booking_id is required"}), 400
        try:
            booking_id = int(booking_id)
            user_id = int(user_id) if user_id else None
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid booking_id or user_id format"}), 400"""

assert p5_old in content, "Target 5 (user_cancel_booking) pattern not found"
content = content.replace(p5_old, p5_new, 1)

# Target 6: admin_cancel_booking (~Line 8987)
p6_old = """def admin_cancel_booking(booking_id):

    \"\"\"Cancel an approved/confirmed booking and trigger refund if needed.\"\"\"

    try:"""

p6_new = """def admin_cancel_booking(booking_id):

    \"\"\"Cancel an approved/confirmed booking and trigger refund if needed.\"\"\"
    is_authorized, err_resp = verify_admin_access()
    if not is_authorized:
        return err_resp

    try:"""

assert p6_old in content, "Target 6 (admin_cancel_booking auth) pattern not found"
content = content.replace(p6_old, p6_new, 1)

p6b_old = """        reason = (request.json or {}).get('reason', 'No reason provided')"""
p6b_new = """        reason = str((request.json or {}).get('reason', 'No reason provided') or 'No reason provided').strip()[:250]"""

assert p6b_old in content, "Target 6b (admin_cancel_booking reason) pattern not found"
content = content.replace(p6b_old, p6b_new, 1)

# Target 7: reject_driver (~Line 9439)
p7_old = """def reject_driver(driver_id):

    \"\"\"Reject a pending driver application.\"\"\"

    data = request.json or {}

    reason = data.get('reason', '')"""

p7_new = """def reject_driver(driver_id):

    \"\"\"Reject a pending driver application.\"\"\"
    is_authorized, err_resp = verify_admin_access()
    if not is_authorized:
        return err_resp

    data = request.json or {}

    reason = str(data.get('reason', '') or '').strip()[:250]"""

assert p7_old in content, "Target 7 (reject_driver) pattern not found"
content = content.replace(p7_old, p7_new, 1)

# Target 8: chat_endpoint (~Line 12130)
p8_old = """def chat_endpoint():
    \"\"\"Smart FAQ chatbot endpoint with Admin toggle controls.\"\"\"
    data = request.json or {}
    message = data.get('message', '').strip()
    user_id = data.get('user_id', None)

    if not message:
        return jsonify({"error": "Message is required"}), 400"""

p8_new = """def chat_endpoint():
    \"\"\"Smart FAQ chatbot endpoint with Admin toggle controls.\"\"\"
    data = request.json or {}
    message = str(data.get('message', '') or '').strip()[:1000]
    user_id = data.get('user_id', None)
    if user_id:
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            user_id = None

    if not message:
        return jsonify({"error": "Message is required"}), 400"""

assert p8_old in content, "Target 8 (chat_endpoint) pattern not found"
content = content.replace(p8_old, p8_new, 1)

# Target 9: add_vehicle (~Line 12797)
p9_old = """        color = data.get('color') or None
        plate = (data.get('plate_number') or '').strip().upper()"""

p9_new = """        color = str(data.get('color') or '').strip()[:50] or None
        mileage_type = 'unlimited' if str(data.get('mileage_type') or 'limited').strip().lower() == 'unlimited' else 'limited'
        fuel_level = str(data.get('fuel_level') or 'Full Tank').strip()[:20]
        year_model_raw = data.get('year_model')
        year_model = None
        if year_model_raw is not None and str(year_model_raw).strip() != '':
            try:
                ym_int = int(year_model_raw)
                if 1950 <= ym_int <= 2030:
                    year_model = ym_int
            except (ValueError, TypeError):
                pass
        plate = (data.get('plate_number') or '').strip().upper()"""

assert p9_old in content, "Target 9 (add_vehicle) pattern not found"
content = content.replace(p9_old, p9_new, 1)

# Target 10: update_vehicle (~Line 12895)
p10_old = """        color = data.get('color') or None
        mileage_type = data.get('mileage_type') or 'limited'
        mileage_km_per_day = data.get('mileage_km_per_day') or 250
        year_model = data.get('year_model') or None"""

p10_new = """        color = str(data.get('color') or '').strip()[:50] or None
        mileage_type = 'unlimited' if str(data.get('mileage_type') or 'limited').strip().lower() == 'unlimited' else 'limited'
        mileage_km_per_day = data.get('mileage_km_per_day') or 250
        year_model_raw = data.get('year_model')
        year_model = None
        if year_model_raw is not None and str(year_model_raw).strip() != '':
            try:
                ym_int = int(year_model_raw)
                if 1950 <= ym_int <= 2030:
                    year_model = ym_int
            except (ValueError, TypeError):
                pass"""

assert p10_old in content, "Target 10 (update_vehicle) pattern not found"
content = content.replace(p10_old, p10_new, 1)

# Target 11: update_license_info (~Line 14363)
p11_old = """        license_number = request.form.get('license_number', '').strip() or None
        license_expiry  = request.form.get('license_expiry', '').strip() or None
        license_type    = request.form.get('license_type', '').strip() or None"""

p11_new = """        license_number = str(request.form.get('license_number', '') or '').strip()[:30] or None
        license_expiry  = str(request.form.get('license_expiry', '') or '').strip()[:20] or None
        license_type    = str(request.form.get('license_type', '') or '').strip()[:30] or None"""

assert p11_old in content, "Target 11 (update_license_info) pattern not found"
content = content.replace(p11_old, p11_new, 1)

# Target 12: chat_mark_read (~Line 16393)
p12_old = """    if not all([receiver_type, receiver_id, sender_type, sender_id]):
        return jsonify({'error': 'Missing fields'}), 400
    try:
        cur = get_cursor()"""

p12_new = """    if not all([receiver_type, receiver_id, sender_type, sender_id]):
        return jsonify({'error': 'Missing fields'}), 400
    allowed_chat_roles = ['admin', 'customer', 'driver', 'staff', 'user', 'system']
    receiver_type = str(receiver_type).strip().lower()
    sender_type = str(sender_type).strip().lower()
    if receiver_type not in allowed_chat_roles or sender_type not in allowed_chat_roles:
        return jsonify({'error': 'Invalid sender or receiver type'}), 400
    try:
        receiver_id = int(receiver_id)
        sender_id = int(sender_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid user ID format'}), 400
    try:
        cur = get_cursor()"""

assert p12_old in content, "Target 12 (chat_mark_read) pattern not found"
content = content.replace(p12_old, p12_new, 1)

# Target 13: update_addon (~Line 16549)
p13_old = """    name = data.get('name', '').strip()
    price = data.get('price_per_day')
    desc = data.get('description', '').strip()"""

p13_new = """    name = str(data.get('name', '') or '').strip()[:100]
    price = data.get('price_per_day')
    desc = str(data.get('description', '') or '').strip()[:250]
    if price is not None:
        try:
            price = max(0.0, min(100000.0, float(price)))
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid price per day'}), 400"""

assert p13_old in content, "Target 13 (update_addon) pattern not found"
content = content.replace(p13_old, p13_new, 1)

# Target 14: edit_penalty (~Line 17597)
p14_old = """def edit_penalty(p_id):
    \"\"\"Admin edits or waives a penalty charge, updating booking balance.\"\"\"
    data = request.json or {}
    new_amount = data.get('amount')
    new_notes = data.get('notes')
    new_charge_type = data.get('charge_type')
    admin_id = data.get('admin_id')"""

p14_new = """def edit_penalty(p_id):
    \"\"\"Admin edits or waives a penalty charge, updating booking balance.\"\"\"
    is_authorized, err_resp = verify_admin_access()
    if not is_authorized:
        return err_resp
    data = request.json or {}
    new_amount = data.get('amount')
    new_notes = str(data.get('notes') or '').strip()[:250] if data.get('notes') else None
    new_charge_type = str(data.get('charge_type') or '').strip()[:50] if data.get('charge_type') else None
    admin_id = data.get('admin_id')"""

assert p14_old in content, "Target 14 (edit_penalty) pattern not found"
content = content.replace(p14_old, p14_new, 1)

with open(BACKEND_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully patched all 14 Round 5 backend targets! Original: {orig_len} chars, New: {len(content)} chars.")
