import sys

BACKEND_APP = 'AutorideSystem/backend/app.py'

with open(BACKEND_APP, 'r', encoding='utf-8') as f:
    content = f.read()

patches = []

# 1. user_forgot_password
old_1 = """    email = data.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'Email is required'}), 400"""

new_1 = """    email = data.get('email', '').strip().lower()
    if not email or len(email) > 60:
        return jsonify({'error': 'A valid email address (max 60 characters) is required'}), 400"""
patches.append(('user_forgot_password', old_1, new_1))

# 2. upload_license
old_2 = """    file = request.files['license']

    if file.filename == '':

        return jsonify({"error": "No selected file"}), 400"""

new_2 = """    file = request.files['license']

    if file.filename == '':

        return jsonify({"error": "No selected file"}), 400

    _img_err = reject_non_image(file, "Driver's license")
    if _img_err:
        return _img_err"""
patches.append(('upload_license', old_2, new_2))

# 3. verify_email
old_3 = """    data = request.json or {}
    email = (data.get('email') or '').strip().lower()
    otp = str(data.get('otp') or '').strip()

    if not email or not otp:
        return jsonify({"error": "Email and OTP are required"}), 400"""

new_3 = """    data = request.json or {}
    email = (data.get('email') or '').strip().lower()
    otp = str(data.get('otp') or '').strip()

    if not email or not otp:
        return jsonify({"error": "Email and OTP are required"}), 400

    if len(email) > 60:
        return jsonify({"error": "Email cannot exceed 60 characters"}), 400

    if len(otp) != 6 or not otp.isdigit():
        return jsonify({"error": "OTP must be exactly 6 digits"}), 400"""
patches.append(('verify_email', old_3, new_3))

# 4. admin_send_custom_push
old_4 = """        data = request.get_json() or {}
        title = data.get('title', '').strip()
        body = data.get('body', '').strip()
        user_id = data.get('user_id')
        broadcast = data.get('broadcast', False)
        
        if not title or not body:
            return jsonify({"error": "Title and body are required"}), 400"""

new_4 = """        data = request.get_json() or {}
        title = (data.get('title', '') or '').strip()[:80]
        body = (data.get('body', '') or '').strip()[:500]
        user_id = data.get('user_id')
        broadcast = data.get('broadcast', False)
        
        if not title or not body:
            return jsonify({"error": "Title and body are required"}), 400"""
patches.append(('admin_send_custom_push', old_4, new_4))

# 5. process_refund
old_5 = """    if not booking_id or not admin_id or not refund_amount:
        return jsonify({"error": "booking_id, admin_id, and refund_amount are required"}), 400"""

new_5 = """    if not booking_id or not admin_id or not refund_amount:
        return jsonify({"error": "booking_id, admin_id, and refund_amount are required"}), 400

    try:
        refund_amount_val = float(refund_amount)
        if refund_amount_val <= 0 or refund_amount_val > 1000000:
            return jsonify({"error": "Refund amount must be greater than 0 and at most 1,000,000"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid refund amount"}), 400

    refund_method = str(refund_method or 'GCash')[:50]
    refund_ref = str(refund_ref or '')[:50]
    refund_note = str(refund_note or '')[:300]"""
patches.append(('process_refund validation', old_5, new_5))

old_5_proof = """        proof_url = None
        if 'proof' in request.files:
            from werkzeug.utils import secure_filename as _sf
            f = request.files['proof']
            if f and f.filename:
                fname = _sf(f"refund_{booking_id}_{int(_dtmod.datetime.now().timestamp())}_{f.filename}")"""

new_5_proof = """        proof_url = None
        if 'proof' in request.files:
            from werkzeug.utils import secure_filename as _sf
            f = request.files['proof']
            if f and f.filename:
                _img_err = reject_non_image(f, 'Proof screenshot')
                if _img_err:
                    return _img_err
                fname = _sf(f"refund_{booking_id}_{int(_dtmod.datetime.now().timestamp())}_{f.filename}")"""
patches.append(('process_refund proof guard', old_5_proof, new_5_proof))

# 6. book() fees safe parsing
old_6 = """            driver_fee = float(data.get('driver_fee', 0.00) or 0.00)
            if rental_type == 'With Driver' and driver_fee <= 0:
                driver_fee = float(755.0 * computed_days)

            delivery_fee = max(0.0, float(data.get('delivery_fee', 0.00) or 0.00))"""

new_6 = """            try:
                driver_fee = max(0.0, float(data.get('driver_fee', 0.00) or 0.00))
            except Exception:
                driver_fee = 0.00
            if rental_type == 'With Driver' and driver_fee <= 0:
                driver_fee = float(755.0 * computed_days)

            try:
                delivery_fee = max(0.0, float(data.get('delivery_fee', 0.00) or 0.00))
            except Exception:
                delivery_fee = 0.00"""
patches.append(('book driver/delivery fee safe cast', old_6, new_6))

# 7. user_change_password
old_7 = """        if not user_id or not new_password:
            return jsonify({'error': 'Missing required fields.'}), 400"""

new_7 = """        if not user_id or not new_password:
            return jsonify({'error': 'Missing required fields.'}), 400

        if len(str(new_password)) < 6 or len(str(new_password)) > 64:
            return jsonify({'error': 'Password must be between 6 and 64 characters.'}), 400"""
patches.append(('user_change_password length check', old_7, new_7))

# 8. mark_booking_paid
old_8 = """    payment_method = (data.get('payment_method') or 'Cash (Over the counter)').strip()
    payment_fee = float(data.get('payment_fee', 0.0) or 0.0)
    payment_fee_percent = float(data.get('payment_fee_percent', 0.0) or 0.0)"""

new_8 = """    payment_method = (data.get('payment_method') or 'Cash (Over the counter)').strip()[:50]
    try:
        payment_fee = max(0.0, float(data.get('payment_fee', 0.0) or 0.0))
        payment_fee_percent = max(0.0, float(data.get('payment_fee_percent', 0.0) or 0.0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid payment fee format"}), 400"""
patches.append(('mark_booking_paid fee safe cast', old_8, new_8))

# 9. update_admin
old_9 = """    requester_id = data.get('requester_id')

    name = data.get('name')

    email = data.get('email')

    password = data.get('password')

    role = data.get('role')

    assigned_location = data.get('assigned_location')"""

new_9 = """    requester_id = data.get('requester_id')

    name = data.get('name')

    email = data.get('email')

    password = data.get('password')

    role = data.get('role')

    assigned_location = data.get('assigned_location')

    if name is not None and len(str(name).strip()) > 50:
        return jsonify({"error": "Admin name cannot exceed 50 characters."}), 400
    if email is not None and (len(str(email).strip()) > 60 or (str(email).strip() and '@' not in str(email))):
        return jsonify({"error": "Admin email must be valid and max 60 characters."}), 400
    if password is not None and str(password).strip():
        if len(str(password)) < 6 or len(str(password)) > 64:
            return jsonify({"error": "Password must be between 6 and 64 characters."}), 400"""
patches.append(('update_admin bounds check', old_9, new_9))

# 10. create_admin
old_10 = """    requester_id = data.get('requester_id') # Matches frontend

    name = data.get('name')

    email = data.get('email')

    password = data.get('password')

    role = data.get('role', 'admin')

    assigned_location = data.get('assigned_location')"""

new_10 = """    requester_id = data.get('requester_id') # Matches frontend

    name = (data.get('name') or '').strip()

    email = (data.get('email') or '').strip().lower()

    password = data.get('password') or ''

    role = data.get('role', 'admin')

    assigned_location = data.get('assigned_location')

    if not name or len(name) > 50:
        return jsonify({"error": "Admin name is required (max 50 characters)."}), 400
    if not email or len(email) > 60 or '@' not in email:
        return jsonify({"error": "Valid admin email is required (max 60 characters)."}), 400
    if len(password) < 6 or len(password) > 64:
        return jsonify({"error": "Password must be between 6 and 64 characters."}), 400"""
patches.append(('create_admin bounds check', old_10, new_10))

# 11. change_admin_password
old_11 = """    if not user_id or not new_password:

        return jsonify({"error": "Missing user_id or password"}), 400"""

new_11 = """    if not user_id or not new_password:

        return jsonify({"error": "Missing user_id or password"}), 400

    if len(str(new_password)) < 6 or len(str(new_password)) > 64:
        return jsonify({"error": "Password must be between 6 and 64 characters"}), 400"""
patches.append(('change_admin_password bounds check', old_11, new_11))

# 12. add_location & update_location
old_12_add = """        name = data.get('name')
        province = data.get('province', '')
        municipality = data.get('municipality', '')
        barangay = data.get('barangay', '')
        delivery_fee = float(data.get('delivery_fee', 0.00))"""

new_12_add = """        name = (data.get('name') or '').strip()[:60]
        province = (data.get('province', '') or '').strip()[:40]
        municipality = (data.get('municipality', '') or '').strip()[:40]
        barangay = (data.get('barangay', '') or '').strip()[:40]
        try:
            delivery_fee = max(0.0, float(data.get('delivery_fee', 0.00) or 0.00))
            if delivery_fee > 10000: delivery_fee = 10000.0
        except (ValueError, TypeError):
            delivery_fee = 0.00"""
patches.append(('add_location bounds check', old_12_add, new_12_add))

old_12_upd = """            name = data.get('name')
            province = data.get('province', '')
            municipality = data.get('municipality', '')
            barangay = data.get('barangay', '')
            delivery_fee = float(data.get('delivery_fee', 0.00))"""

new_12_upd = """            name = (data.get('name') or '').strip()[:60]
            province = (data.get('province', '') or '').strip()[:40]
            municipality = (data.get('municipality', '') or '').strip()[:40]
            barangay = (data.get('barangay', '') or '').strip()[:40]
            try:
                delivery_fee = max(0.0, float(data.get('delivery_fee', 0.00) or 0.00))
                if delivery_fee > 10000: delivery_fee = 10000.0
            except (ValueError, TypeError):
                delivery_fee = 0.00"""
patches.append(('update_location bounds check', old_12_upd, new_12_upd))

# 13. update_license_info
old_13 = """        if 'license' in request.files:
            file = request.files['license']
            if file.filename:
                filename = f"license_{user_id}_{int(datetime.now().timestamp())}.jpg\""""

new_13 = """        if 'license' in request.files:
            file = request.files['license']
            if file.filename:
                _img_err = reject_non_image(file, "Driver's license")
                if _img_err:
                    return _img_err
                filename = f"license_{user_id}_{int(datetime.now().timestamp())}.jpg\""""
patches.append(('update_license_info image check', old_13, new_13))

# 14. save_license_details upload_img
old_14 = """        def upload_img(file_key, prefix):
            if file_key in request.files and request.files[file_key].filename:
                file = request.files[file_key]
                
                # Check file size (max 5MB)
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                
                if file_size > 5 * 1024 * 1024:  # 5MB limit
                    raise ValueError(f"File {file_key} is too large. Maximum size is 5MB.")"""

new_14 = """        def upload_img(file_key, prefix):
            if file_key in request.files and request.files[file_key].filename:
                file = request.files[file_key]
                if not is_allowed_image(file):
                    raise ValueError(f"File {file_key} must be an image file (jpg, png, gif, webp).")
                
                # Check file size (max 5MB)
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                
                if file_size > 5 * 1024 * 1024:  # 5MB limit
                    raise ValueError(f"File {file_key} is too large. Maximum size is 5MB.")"""
patches.append(('save_license_details upload_img validation', old_14, new_14))

# 15. create_addon
old_15 = """def create_addon():
    \"\"\"Create a new rental addon. Admin only validation.\"\"\"
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    price = data.get('price_per_day')
    desc = data.get('description', '').strip()
    admin_id = data.get('admin_id')

    if not name or price is None or not admin_id:
        return jsonify({'error': 'Name, price per day, and admin_id are required.'}), 400"""

new_15 = """def create_addon():
    \"\"\"Create a new rental addon. Admin only validation.\"\"\"
    data = request.get_json(silent=True) or {}
    name = (data.get('name', '') or '').strip()[:50]
    price = data.get('price_per_day')
    desc = (data.get('description', '') or '').strip()[:250]
    admin_id = data.get('admin_id')

    if not name or price is None or not admin_id:
        return jsonify({'error': 'Name, price per day, and admin_id are required.'}), 400

    try:
        price_val = max(0.0, min(10000.0, float(price)))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid price per day.'}), 400"""
patches.append(('create_addon validation', old_15, new_15))

old_15_sql = """        cur.execute(\"\"\"
            INSERT INTO addons (name, price_per_day, description)
            VALUES (%s, %s, %s) RETURNING id
        \"\"\", (name, float(price), desc))"""

new_15_sql = """        cur.execute(\"\"\"
            INSERT INTO addons (name, price_per_day, description)
            VALUES (%s, %s, %s) RETURNING id
        \"\"\", (name, price_val, desc))"""
patches.append(('create_addon sql price_val', old_15_sql, new_15_sql))

# 16. create_insurance_option
old_16 = """def create_insurance_option():
    \"\"\"Create a new insurance package. Super Admin / Admin validation.\"\"\"
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    price = data.get('price_per_day')
    desc = data.get('description', '').strip()
    admin_id = data.get('admin_id')

    if not name or price is None or not admin_id:
        return jsonify({'error': 'Name, price per day, and admin_id are required.'}), 400"""

new_16 = """def create_insurance_option():
    \"\"\"Create a new insurance package. Super Admin / Admin validation.\"\"\"
    data = request.get_json(silent=True) or {}
    name = (data.get('name', '') or '').strip()[:50]
    price = data.get('price_per_day')
    desc = (data.get('description', '') or '').strip()[:250]
    admin_id = data.get('admin_id')

    if not name or price is None or not admin_id:
        return jsonify({'error': 'Name, price per day, and admin_id are required.'}), 400

    try:
        price_val = max(0.0, min(20000.0, float(price)))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid price per day.'}), 400"""
patches.append(('create_insurance_option validation', old_16, new_16))

old_16_sql = """        cur.execute(\"\"\"
            INSERT INTO insurance_options (name, price_per_day, description, is_active)
            VALUES (%s, %s, %s, TRUE) RETURNING id
        \"\"\", (name, float(price), desc))"""

new_16_sql = """        cur.execute(\"\"\"
            INSERT INTO insurance_options (name, price_per_day, description, is_active)
            VALUES (%s, %s, %s, TRUE) RETURNING id
        \"\"\", (name, price_val, desc))"""
patches.append(('create_insurance_option sql price_val', old_16_sql, new_16_sql))

# 17. update_booking_quick_pricing
old_17 = """        total_price = float(data.get('total_price') if data.get('total_price') is not None else (b['total_price'] or 0.0))
        amount_paid = float(data.get('amount_paid') if data.get('amount_paid') is not None else (b['amount_paid'] or 0.0))
        
        if data.get('balance_amount') is not None:
            balance_amount = float(data.get('balance_amount'))
        else:
            balance_amount = max(0.0, total_price - amount_paid)"""

new_17 = """        try:
            total_price = max(0.0, float(data.get('total_price') if data.get('total_price') is not None else (b['total_price'] or 0.0)))
            amount_paid = max(0.0, float(data.get('amount_paid') if data.get('amount_paid') is not None else (b['amount_paid'] or 0.0)))
            if data.get('balance_amount') is not None:
                balance_amount = max(0.0, float(data.get('balance_amount')))
            else:
                balance_amount = max(0.0, total_price - amount_paid)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid price or amount values"}), 400"""
patches.append(('update_booking_quick_pricing safe casts', old_17, new_17))

# Verify all patches match uniquely
all_matched = True
for label, old_text, _ in patches:
    cnt = content.count(old_text)
    if cnt != 1:
        print(f"FAILED MATCH: [{label}] found {cnt} occurrences!")
        all_matched = False
    else:
        print(f"MATCH OK: [{label}]")

if not all_matched:
    print("\nAborting: Not all patches matched uniquely.")
    sys.exit(1)

for label, old_text, new_text in patches:
    content = content.replace(old_text, new_text, 1)

with open(BACKEND_APP, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nSUCCESS: All {len(patches)} backend validation patches successfully applied!")
