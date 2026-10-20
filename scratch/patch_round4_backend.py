import re
import sys

BACKEND_PATH = "backend/app.py"

with open(BACKEND_PATH, "r", encoding="utf-8") as f:
    content = f.read()

orig_len = len(content)

# Target 1: admin_verify_user (~Line 2907)
# Ensure status is in (0, 1, 2)
p1_old = """    # Ensure correct types
    try:
        user_id = int(user_id)
        status  = int(status)
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid parameter types: {e}"}), 400"""

p1_new = """    # Ensure correct types
    try:
        user_id = int(user_id)
        status  = int(status)
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid parameter types: {e}"}), 400

    if status not in (0, 1, 2):
        return jsonify({"error": "Invalid status: must be 2 (Verified), 1 (Pending), or 0 (Rejected)"}), 400"""

assert p1_old in content, "Target 1 (admin_verify_user) pattern not found"
content = content.replace(p1_old, p1_new, 1)

# Target 2: apply_driver (~Line 9505)
# Add bounds, typecast, and file validation
p2_old = """    user_id = request.form.get('user_id')

    full_name = request.form.get('full_name')

    license_number = request.form.get('license_number')

    contact_info = request.form.get('contact_info')



    if not all([user_id, full_name, license_number, contact_info]):

        return jsonify({"error": "Missing application details"}), 400



    if 'license_document' not in request.files or request.files['license_document'].filename == '':

        return jsonify({"error": "Driver's license document is required"}), 400



    try:"""

p2_new = """    user_id = request.form.get('user_id')

    full_name = request.form.get('full_name')

    license_number = request.form.get('license_number')

    contact_info = request.form.get('contact_info')



    if not all([user_id, full_name, license_number, contact_info]):

        return jsonify({"error": "Missing application details"}), 400

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid user_id"}), 400

    full_name = str(full_name).strip()[:50]
    license_number = str(license_number).strip()[:30]
    contact_info = str(contact_info).strip()[:30]

    if 'license_document' not in request.files or request.files['license_document'].filename == '':

        return jsonify({"error": "Driver's license document is required"}), 400

    lic_file = request.files['license_document']
    _img_err = reject_non_image(lic_file, "Driver's license document", allow_pdf=True)
    if _img_err:
        return _img_err

    try:"""

assert p2_old in content, "Target 2 (apply_driver) pattern not found"
content = content.replace(p2_old, p2_new, 1)

# Target 3: update_driver_booking_status (~Line 9713)
# Whitelist driver booking status
p3_old = """    if not user_id or not new_status:

        return jsonify({"error": "user_id and status required"}), 400

        

    try:"""

p3_new = """    if not user_id or not new_status:

        return jsonify({"error": "user_id and status required"}), 400

    new_status = str(new_status).strip()
    allowed_driver_statuses = ['Arrived', 'En Route', 'Picked Up', 'Completed', 'Cancelled']
    if new_status not in allowed_driver_statuses:
        return jsonify({"error": f"Invalid driver booking status. Allowed: {', '.join(allowed_driver_statuses)}"}), 400

    try:"""

assert p3_old in content, "Target 3 (update_driver_booking_status) pattern not found"
content = content.replace(p3_old, p3_new, 1)

# Target 4: submit_support (~Line 10663)
# Bounds check on name, email, subject, message
p4_old = """    if not all([name, subject, message]):

        return jsonify({"error": "Missing required support fields"}), 400

        

    try:"""

p4_new = """    if not all([name, subject, message]):

        return jsonify({"error": "Missing required support fields"}), 400

    name = str(name).strip()[:50]
    email = str(email or '').strip()[:100]
    subject = str(subject).strip()[:150]
    message = str(message).strip()[:2000]

    try:"""

assert p4_old in content, "Target 4 (submit_support) pattern not found"
content = content.replace(p4_old, p4_new, 1)

# Target 5: resolve_support_ticket (~Line 10741)
# Whitelist status and cap admin_reply
p5_old = """def resolve_support_ticket(ticket_id):

    data = request.json

    reply = data.get('admin_reply', '')

    status = data.get('status', 'resolved')

    

    try:"""

p5_new = """def resolve_support_ticket(ticket_id):
    is_authorized, err_resp = verify_admin_access()
    if not is_authorized:
        return err_resp

    data = request.json or {}

    reply = str(data.get('admin_reply', '') or '').strip()[:2000]

    status = str(data.get('status', 'resolved') or 'resolved').strip()
    allowed_ticket_statuses = ['open', 'in_progress', 'resolved', 'closed', 'Open', 'In Progress', 'Resolved', 'Closed']
    if status not in allowed_ticket_statuses:
        return jsonify({"error": f"Invalid ticket status. Allowed: {', '.join(allowed_ticket_statuses)}"}), 400

    try:"""

assert p5_old in content, "Target 5 (resolve_support_ticket) pattern not found"
content = content.replace(p5_old, p5_new, 1)

# Target 6: verify_user (~Line 11808)
p6_old = """def verify_user():

    data = request.json or {}

    user_id = data.get('user_id')

    status = data.get('status') # 1 for Approve, 2 for Reject

    

    if not user_id or status is None:

        return jsonify({"error": "user_id and status are required"}), 400

        

    try:"""

p6_new = """def verify_user():
    is_authorized, err_resp = verify_admin_access()
    if not is_authorized:
        return err_resp

    data = request.json or {}

    user_id = data.get('user_id')

    status = data.get('status') # 1 for Approve, 2 for Reject

    if not user_id or status is None:

        return jsonify({"error": "user_id and status are required"}), 400

    try:
        user_id = int(user_id)
        status = int(status)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid user_id or status type"}), 400

    if status not in (0, 1, 2):
        return jsonify({"error": "Status must be 1 (Approve), 2 (Reject), or 0"}), 400

    try:"""

assert p6_old in content, "Target 6 (verify_user) pattern not found"
content = content.replace(p6_old, p6_new, 1)

# Target 7: update_vehicle_status (~Line 12953)
p7_old = """def update_vehicle_status(vehicle_id):
    data = request.json or request.form
    new_status = data.get('status')
    if not new_status:
        return jsonify({"error": "Status is required"}), 400
    try:"""

p7_new = """def update_vehicle_status(vehicle_id):
    is_authorized, err_resp = verify_admin_access()
    if not is_authorized:
        return err_resp
    data = request.json or request.form or {}
    new_status = str(data.get('status', '') or '').strip()
    if not new_status:
        return jsonify({"error": "Status is required"}), 400
    allowed_veh_statuses = ['Available', 'Rented', 'Maintenance', 'Unavailable']
    if new_status not in allowed_veh_statuses:
        return jsonify({"error": f"Invalid vehicle status. Allowed: {', '.join(allowed_veh_statuses)}"}), 400
    try:"""

assert p7_old in content, "Target 7 (update_vehicle_status) pattern not found"
content = content.replace(p7_old, p7_new, 1)

# Target 8: update_vehicle_rate (~Line 12975)
p8_old = """        daily_rate = float(dr_str)
        if daily_rate < 0:
            return jsonify({"error": "Daily rate must be non-negative"}), 400"""

p8_new = """        daily_rate = float(dr_str)
        if daily_rate < 0 or daily_rate > 1000000:
            return jsonify({"error": "Daily rate must be between 0 and 1,000,000 PHP"}), 400"""

assert p8_old in content, "Target 8 (update_vehicle_rate) pattern not found"
content = content.replace(p8_old, p8_new, 1)

# Also add verify_admin_access to update_vehicle_rate
p8b_old = """def update_vehicle_rate(vehicle_id):
    data = request.get_json(silent=True) or request.form or {}"""

p8b_new = """def update_vehicle_rate(vehicle_id):
    is_authorized, err_resp = verify_admin_access()
    if not is_authorized:
        return err_resp
    data = request.get_json(silent=True) or request.form or {}"""

assert p8b_old in content, "Target 8b (update_vehicle_rate auth) pattern not found"
content = content.replace(p8b_old, p8b_new, 1)

# Target 9: add_admin_blackout_date (~Line 16959)
p9_old = """    if not all([start_date, end_date, reason, created_by]):
        return jsonify({'error': 'Missing required fields'}), 400
    if not check_staff_permission(created_by, 'perm_blackout_dates'):
        return jsonify({'error': 'Unauthorized. Blackout dates management permission required.'}), 403
        
    try:"""

p9_new = """    if not all([start_date, end_date, reason, created_by]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        from datetime import datetime as _dt
        d1 = _dt.strptime(str(start_date).strip(), '%Y-%m-%d')
        d2 = _dt.strptime(str(end_date).strip(), '%Y-%m-%d')
        if d1 > d2:
            return jsonify({'error': 'Start date cannot be after end date'}), 400
        if d1.year < 2020 or d2.year > 2099:
            return jsonify({'error': 'Dates must be between 2020 and 2099'}), 400
    except ValueError:
        return jsonify({'error': 'Dates must be in valid YYYY-MM-DD format'}), 400

    reason = str(reason).strip()[:100]
    affected_vehicles = str(affected_vehicles).strip()[:100]

    try:
        created_by = int(created_by)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid created_by admin_id'}), 400

    if not check_staff_permission(created_by, 'perm_blackout_dates'):
        return jsonify({'error': 'Unauthorized. Blackout dates management permission required.'}), 403
        
    try:"""

assert p9_old in content, "Target 9 (add_admin_blackout_date) pattern not found"
content = content.replace(p9_old, p9_new, 1)

# Target 10: import_fleet_calendar_preview (~Line 17224)
p10_old = """        if 'file' in request.files:
            file_obj = request.files['file']
            if not file_obj or file_obj.filename == '':
                return jsonify({'error': 'No file uploaded'}), 400
            raw_records = fleet_import.parse_fleet_excel_file(file_obj)"""

p10_new = """        if 'file' in request.files:
            file_obj = request.files['file']
            if not file_obj or file_obj.filename == '':
                return jsonify({'error': 'No file uploaded'}), 400
            if not file_obj.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
                return jsonify({'error': 'Uploaded file must be an Excel file (.xlsx, .xls) or CSV'}), 400
            file_obj.seek(0, os.SEEK_END)
            f_size = file_obj.tell()
            file_obj.seek(0)
            if f_size > 15 * 1024 * 1024:
                return jsonify({'error': 'Excel file exceeds maximum allowed size (15 MB)'}), 400
            raw_records = fleet_import.parse_fleet_excel_file(file_obj)"""

assert p10_old in content, "Target 10 (import_fleet_calendar_preview) pattern not found"
content = content.replace(p10_old, p10_new, 1)

# Target 11: update_booking_quick_pricing (~Line 17331)
p11_old = """        try:
            total_price = max(0.0, float(data.get('total_price') if data.get('total_price') is not None else (b['total_price'] or 0.0)))
            amount_paid = max(0.0, float(data.get('amount_paid') if data.get('amount_paid') is not None else (b['amount_paid'] or 0.0)))
            if data.get('balance_amount') is not None:
                balance_amount = max(0.0, float(data.get('balance_amount')))
            else:
                balance_amount = max(0.0, total_price - amount_paid)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid price or amount values"}), 400

        payment_status = data.get('payment_status')
        if not payment_status:
            if balance_amount <= 0 and total_price > 0:
                payment_status = 'Paid'
            elif amount_paid > 0 and balance_amount > 0:
                payment_status = 'Partially Paid'
            else:
                payment_status = b.get('payment_status') or 'Unpaid'

        payment_method = data.get('payment_method') or b.get('payment_method') or 'Cash'
        calendar_color = data.get('calendar_color') if 'calendar_color' in data else (b.get('calendar_color') or '')
        calendar_color = str(calendar_color or '').strip()"""

p11_new = """        try:
            total_price = min(10000000.0, max(0.0, float(data.get('total_price') if data.get('total_price') is not None else (b['total_price'] or 0.0))))
            amount_paid = min(10000000.0, max(0.0, float(data.get('amount_paid') if data.get('amount_paid') is not None else (b['amount_paid'] or 0.0))))
            if data.get('balance_amount') is not None:
                balance_amount = min(10000000.0, max(0.0, float(data.get('balance_amount'))))
            else:
                balance_amount = max(0.0, total_price - amount_paid)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid price or amount values"}), 400

        payment_status = data.get('payment_status')
        if not payment_status:
            if balance_amount <= 0 and total_price > 0:
                payment_status = 'Paid'
            elif amount_paid > 0 and balance_amount > 0:
                payment_status = 'Partially Paid'
            else:
                payment_status = b.get('payment_status') or 'Unpaid'
        else:
            payment_status = str(payment_status).strip()
            allowed_pay_statuses = ['Paid', 'Partially Paid', 'Unpaid', 'Refunded', 'Cancelled']
            if payment_status not in allowed_pay_statuses:
                return jsonify({"error": f"Invalid payment status. Allowed: {', '.join(allowed_pay_statuses)}"}), 400

        payment_method = str(data.get('payment_method') or b.get('payment_method') or 'Cash').strip()[:50]
        calendar_color = data.get('calendar_color') if 'calendar_color' in data else (b.get('calendar_color') or '')
        calendar_color = str(calendar_color or '').strip()[:20]"""

assert p11_old in content, "Target 11 (update_booking_quick_pricing) pattern not found"
content = content.replace(p11_old, p11_new, 1)

# Target 12: add_booking_penalty (~Line 17459)
p12_old = """def add_booking_penalty(booking_id):
    data = request.json or {}
    charge_type = data.get('charge_type')
    amount = data.get('amount')
    notes = data.get('notes')
    admin_id = data.get('admin_id')
    
    if not charge_type or amount is None:
        return jsonify({'error': 'Charge type and amount required'}), 400"""

p12_new = """def add_booking_penalty(booking_id):
    is_authorized, err_resp = verify_admin_access()
    if not is_authorized:
        return err_resp

    data = request.json or {}
    charge_type = data.get('charge_type')
    amount = data.get('amount')
    notes = data.get('notes')
    admin_id = data.get('admin_id')
    
    if not charge_type or amount is None:
        return jsonify({'error': 'Charge type and amount required'}), 400

    charge_type = str(charge_type).strip()[:50]
    try:
        admin_id = int(admin_id) if admin_id else None
    except (ValueError, TypeError):
        admin_id = None"""

assert p12_old in content, "Target 12 (add_booking_penalty) pattern not found"
content = content.replace(p12_old, p12_new, 1)

with open(BACKEND_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully patched all 12 backend targets! Original: {orig_len} chars, New: {len(content)} chars.")
