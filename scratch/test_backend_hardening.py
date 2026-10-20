with open('backend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

patches = [
    # 1. reject_non_image size check
    (
        '''def reject_non_image(file_storage, field_name='file'):
    """Return a 400 JSON error if the file is not an allowed image, else None."""
    if file_storage and file_storage.filename and file_storage.filename != '':
        if not is_allowed_image(file_storage):
            from flask import jsonify
            return jsonify({'error': f'{field_name} must be an image file (jpg, png, gif, webp).'}), 400
    return None''',
        '''def reject_non_image(file_storage, field_name='file', max_mb=15):
    """Return a 400 JSON error if the file is not an allowed image or exceeds max_mb, else None."""
    if file_storage and file_storage.filename and file_storage.filename != '':
        if not is_allowed_image(file_storage):
            from flask import jsonify
            return jsonify({'error': f'{field_name} must be an image file (jpg, png, gif, webp).'}), 400
        try:
            file_storage.seek(0, 2)
            size = file_storage.tell()
            file_storage.seek(0)
            if size > max_mb * 1024 * 1024:
                from flask import jsonify
                return jsonify({'error': f'{field_name} exceeds {max_mb} MB limit.'}), 400
        except Exception:
            pass
    return None'''
    ),
    # 2. register password & email length check
    (
        '''    if not email or not is_gmail(email):

        return jsonify({"error": "Only @gmail.com emails are allowed for registration."}), 400''',
        '''    if not email or not is_gmail(email):

        return jsonify({"error": "Only @gmail.com emails are allowed for registration."}), 400

    if len(email) > 60:
        return jsonify({"error": "Email cannot exceed 60 characters."}), 400

    if not password or len(password) < 6 or len(password) > 64:
        return jsonify({"error": "Password must be between 6 and 64 characters."}), 400'''
    ),
    # 3. add_review comment length
    (
        '''    if not user_id or not rating:
        return jsonify({"error": "user_id and rating are required"}), 400''',
        '''    if not user_id or not rating:
        return jsonify({"error": "user_id and rating are required"}), 400
    if comment and len(comment) > 300:
        return jsonify({"error": "Review comment cannot exceed 300 characters"}), 400'''
    ),
    # 4. create_walkin_booking input bounds
    (
        '''        if not customer_name:
            return jsonify({"error": "Customer name is required"}), 400''',
        '''        if not customer_name:
            return jsonify({"error": "Customer name is required"}), 400
        if len(customer_name) > 50:
            return jsonify({"error": "Customer name cannot exceed 50 characters"}), 400
        if len(customer_phone) > 15:
            return jsonify({"error": "Customer phone cannot exceed 15 characters"}), 400
        if len(customer_address) > 100:
            return jsonify({"error": "Customer address cannot exceed 100 characters"}), 400
        if len(emergency_name) > 50:
            return jsonify({"error": "Emergency contact name cannot exceed 50 characters"}), 400
        if len(emergency_phone) > 15:
            return jsonify({"error": "Emergency contact phone cannot exceed 15 characters"}), 400
        if len(emergency_rel) > 30:
            return jsonify({"error": "Emergency relationship cannot exceed 30 characters"}), 400'''
    ),
    # 5. submit_inspection mileage & notes bounds
    (
        '''        try:
            new_mileage = float(str(mileage).strip())
            if new_mileage < 0:
                return jsonify({"error": "Mileage must be a positive number."}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid mileage number format."}), 400''',
        '''        try:
            new_mileage = float(str(mileage).strip())
            if new_mileage < 0 or new_mileage > 999999:
                return jsonify({"error": "Mileage must be between 0 and 999,999 km."}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid mileage number format."}), 400

        if notes and len(str(notes)) > 300:
            return jsonify({"error": "Inspection notes cannot exceed 300 characters."}), 400
        if fuel_charge_notes and len(str(fuel_charge_notes)) > 150:
            return jsonify({"error": "Fuel charge notes cannot exceed 150 characters."}), 400'''
    ),
    # 6. submit_refund_details bounds
    (
        '''        if not refund_channel or not refund_account_name or not refund_account_number:
            return jsonify({"error": "Refund channel, account name, and account number are required."}), 400''',
        '''        if not refund_channel or not refund_account_name or not refund_account_number:
            return jsonify({"error": "Refund channel, account name, and account number are required."}), 400
        if len(refund_account_name) > 50:
            return jsonify({"error": "Account name cannot exceed 50 characters."}), 400
        if len(refund_account_number) > 20:
            return jsonify({"error": "Account number cannot exceed 20 characters."}), 400
        if refund_notes and len(refund_notes) > 200:
            return jsonify({"error": "Notes cannot exceed 200 characters."}), 400'''
    ),
    # 7. admin_create_newsletter bounds
    (
        '''    if not title or not content:
        return jsonify({"error": "Title and content are required"}), 400''',
        '''    if not title or not content:
        return jsonify({"error": "Title and content are required"}), 400
    if len(title) > 80:
        return jsonify({"error": "Title cannot exceed 80 characters"}), 400
    if len(content) > 1000:
        return jsonify({"error": "Content cannot exceed 1000 characters"}), 400
    if promo_code and len(promo_code) > 15:
        return jsonify({"error": "Promo code cannot exceed 15 characters"}), 400
    if discount_val is not None and (discount_val < 1 or discount_val > 90):
        return jsonify({"error": "Discount must be between 1 and 90 percent"}), 400'''
    ),
    # 8. update_super_admin_profile bounds
    (
        '''        if not pw_ok:
            return jsonify({"error": "Current password is incorrect."}), 401''',
        '''        if not pw_ok:
            return jsonify({"error": "Current password is incorrect."}), 401

        if new_email and len(new_email) > 60:
            return jsonify({"error": "Email cannot exceed 60 characters."}), 400
        if new_password and (len(new_password) < 6 or len(new_password) > 64):
            return jsonify({"error": "New password must be between 6 and 64 characters."}), 400'''
    ),
    # 9. add_vehicle plate & daily rate bounds
    (
        '''        daily_rate_raw = data.get('daily_rate')
        daily_rate = None''',
        '''        plate = (data.get('plate_number') or '').strip().upper()
        if not plate or len(plate) > 8:
            return jsonify({"error": "Plate number is required and cannot exceed 8 characters"}), 400
        if color and len(color) > 30:
            return jsonify({"error": "Color cannot exceed 30 characters"}), 400

        daily_rate_raw = data.get('daily_rate')
        daily_rate = None'''
    ),
    # 10. chat_send length check
    (
        '''    if not all([sender_type, sender_id, receiver_type, receiver_id, message]):
        return jsonify({'error': 'Missing required fields'}), 400''',
        '''    if not all([sender_type, sender_id, receiver_type, receiver_id, message]):
        return jsonify({'error': 'Missing required fields'}), 400
    if len(message) > 250:
        return jsonify({'error': 'Message cannot exceed 250 characters'}), 400'''
    ),
    # 11. add_booking_penalty bounds
    (
        '''    if not charge_type or amount is None:
        return jsonify({'error': 'Charge type and amount required'}), 400''',
        '''    if not charge_type or amount is None:
        return jsonify({'error': 'Charge type and amount required'}), 400
    try:
        amt_float = float(amount)
        if amt_float < 0 or amt_float > 100000:
            return jsonify({'error': 'Penalty amount must be between 0 and 100,000 PHP'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid penalty amount'}), 400
    if notes and len(str(notes)) > 250:
        return jsonify({'error': 'Notes cannot exceed 250 characters'}), 400'''
    )
]

for idx, (t, r) in enumerate(patches, 1):
    cnt = content.count(t)
    if cnt == 1:
        print(f"[{idx}] OK: exact 1 match")
    else:
        print(f"[{idx}] ERROR: found {cnt} matches for {repr(t[:40])}")
