import sys

BACKEND_PATH = "backend/app.py"

with open(BACKEND_PATH, "r", encoding="utf-8") as f:
    content = f.read()

orig_len = len(content)

# Target 1: Refund proof upload MIME validation (~Line 4646)
p1_old = """    file = request.files['proof']

    if file.filename == '':

        return jsonify({"error": "No selected file"}), 400

        

    try:"""

p1_new = """    file = request.files['proof']

    if file.filename == '':

        return jsonify({"error": "No selected file"}), 400

    _img_err = reject_non_image(file, "Refund proof", allow_pdf=True)
    if _img_err:
        return _img_err

    try:"""

assert p1_old in content, "Target 1 (refund proof) pattern not found"
content = content.replace(p1_old, p1_new, 1)

# Target 2: Walk-in pricing calculations & bounds (~Line 7569)
p2_old = """        daily_rate = float(veh['daily_rate'] or 0.0)
        base_price = float(data.get('base_price') or (daily_rate * days))
        addon_price = max(0.0, float(data.get('addon_price') or 0.0))
        driver_fee = max(0.0, float(data.get('driver_fee') or 0.0))
        delivery_fee = max(0.0, float(data.get('delivery_fee') or 0.0))
        discount_amount = max(0.0, float(data.get('discount_amount') or 0.0))

        default_total = max(0.0, (base_price + addon_price + driver_fee + delivery_fee) - discount_amount)
        total_price = float(data.get('total_price') if data.get('total_price') is not None else default_total)

        amount_paid = max(0.0, float(data.get('amount_paid') or 0.0))
        balance_amount = max(0.0, float(data.get('balance_amount') if data.get('balance_amount') is not None else max(0.0, total_price - amount_paid)))

        payment_method = (data.get('payment_method') or 'Cash').strip()
        payment_status = (data.get('payment_status') or ('Paid' if (amount_paid >= total_price and total_price > 0) else ('Partial' if amount_paid > 0 else 'Unpaid'))).strip()
        payment_type = (data.get('payment_type') or ('Full' if amount_paid >= total_price else 'Downpayment')).strip()

        # Status: Walk-in can be directly Confirmed or Picked Up
        status = (data.get('status') or 'Confirmed').strip()
        rental_type = (data.get('rental_type') or 'Self Drive').strip()
        pickup_location = (data.get('pickup_location') or 'Main Office / Garage').strip()
        destination = (data.get('destination') or '').strip()
        rental_purpose = (data.get('rental_purpose') or 'Walk-in Counter Rental').strip()"""

p2_new = """        try:
            daily_rate = min(1000000.0, max(0.0, float(veh['daily_rate'] or 0.0)))
            base_price = min(10000000.0, max(0.0, float(data.get('base_price') or (daily_rate * days))))
            addon_price = min(10000000.0, max(0.0, float(data.get('addon_price') or 0.0)))
            driver_fee = min(10000000.0, max(0.0, float(data.get('driver_fee') or 0.0)))
            delivery_fee = min(10000000.0, max(0.0, float(data.get('delivery_fee') or 0.0)))
            discount_amount = min(10000000.0, max(0.0, float(data.get('discount_amount') or 0.0)))

            default_total = max(0.0, (base_price + addon_price + driver_fee + delivery_fee) - discount_amount)
            total_price = min(10000000.0, max(0.0, float(data.get('total_price') if data.get('total_price') is not None else default_total)))

            amount_paid = min(10000000.0, max(0.0, float(data.get('amount_paid') or 0.0)))
            balance_amount = min(10000000.0, max(0.0, float(data.get('balance_amount') if data.get('balance_amount') is not None else max(0.0, total_price - amount_paid))))
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid numerical values in pricing or payment amounts"}), 400

        payment_method = str(data.get('payment_method') or 'Cash').strip()[:50]
        payment_status = str(data.get('payment_status') or ('Paid' if (amount_paid >= total_price and total_price > 0) else ('Partial' if amount_paid > 0 else 'Unpaid'))).strip()
        allowed_pay_statuses = ['Paid', 'Partial', 'Partially Paid', 'Unpaid', 'Refunded', 'Cancelled']
        if payment_status not in allowed_pay_statuses:
            payment_status = 'Unpaid'
        payment_type = str(data.get('payment_type') or ('Full' if amount_paid >= total_price else 'Downpayment')).strip()[:30]

        # Status: Walk-in can be directly Confirmed or Picked Up
        status = str(data.get('status') or 'Confirmed').strip()
        allowed_walkin_statuses = ['Pending', 'Confirmed', 'Approved', 'Picked Up', 'Completed', 'Cancelled']
        if status not in allowed_walkin_statuses:
            status = 'Confirmed'
        rental_type = str(data.get('rental_type') or 'Self Drive').strip()[:30]
        pickup_location = str(data.get('pickup_location') or 'Main Office / Garage').strip()[:150]
        destination = str(data.get('destination') or '').strip()[:100]
        rental_purpose = str(data.get('rental_purpose') or 'Walk-in Counter Rental').strip()[:100]"""

assert p2_old in content, "Target 2 (walkin pricing) pattern not found"
content = content.replace(p2_old, p2_new, 1)

# Target 3: Expense receipt upload MIME validation & amount clamp (~Line 17019)
p3_old = """    if 'proof_image' in request.files:
        file = request.files['proof_image']
        if file.filename != '':
            ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'jpg'"""

p3_new = """    if 'proof_image' in request.files:
        file = request.files['proof_image']
        if file.filename != '':
            _img_err = reject_non_image(file, "Expense receipt", allow_pdf=True)
            if _img_err:
                return _img_err
            ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'jpg'"""

assert p3_old in content, "Target 3 (expense receipt) pattern not found"
content = content.replace(p3_old, p3_new, 1)

with open(BACKEND_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully applied final audit patches! Original: {orig_len} chars, New: {len(content)} chars.")
