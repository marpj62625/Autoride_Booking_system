# -*- coding: utf-8 -*-
# This file uses only ASCII characters
"""
Adds Extend Booking feature backend endpoints
"""
import re

# ???????????????????????????????????????????????
#  1. BACKEND — /bookings/<id>/extend endpoint
# ???????????????????????????????????????????????
with open('backend/app.py', 'rb') as f:
    app_content = f.read().decode('utf-8', errors='replace')

# Insert after the receipt endpoint (near end of file, before last route)
# Find a good insertion point — after /bookings/<id>/receipt
insert_after = "@app.route('/chat/send', methods=['POST'])"
idx = app_content.find(insert_after)

extend_endpoint = '''
@app.route('/bookings/<int:booking_id>/extend', methods=['POST'])
def extend_booking(booking_id):
    """
    Customer requests a booking extension.
    Stores extension request with payment proof; admin must approve.
    If admin rejects, refund is noted for upon-return processing.
    """
    try:
        data = request.form if not request.is_json else request.get_json()
        new_end_date      = data.get('new_end_date')
        extension_price   = data.get('extension_price')
        payment_method    = data.get('payment_method', 'Cash (Over the counter)')
        reference_number  = data.get('reference_number', '')

        if not new_end_date or not extension_price:
            return jsonify({"error": "new_end_date and extension_price are required"}), 400

        cur = get_cursor()

        # 1. Validate booking exists and is active
        cur.execute("SELECT id, user_id, end_date, status, vehicle_id FROM bookings WHERE id = %s", (booking_id,))
        booking = cur.fetchone()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        if booking['status'] not in ('Picked Up', 'Ongoing', 'Confirmed', 'Approved'):
            return jsonify({"error": "Booking cannot be extended in its current status"}), 400

        # 2. Ensure extension table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS booking_extensions (
                id                BIGSERIAL PRIMARY KEY,
                booking_id        INTEGER NOT NULL REFERENCES bookings(id),
                requested_by      INTEGER NOT NULL,
                original_end_date DATE NOT NULL,
                new_end_date      DATE NOT NULL,
                extension_days    INTEGER NOT NULL,
                extension_price   NUMERIC(12,2) NOT NULL,
                payment_method    VARCHAR(100),
                reference_number  VARCHAR(200),
                payment_proof_url TEXT,
                status            VARCHAR(20) DEFAULT 'pending',
                admin_note        TEXT,
                created_at        TIMESTAMPTZ DEFAULT NOW(),
                updated_at        TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # 3. Handle payment proof upload
        payment_proof_url = None
        if 'payment_proof' in request.files:
            from werkzeug.utils import secure_filename
            import os, uuid
            f_file = request.files['payment_proof']
            if f_file and f_file.filename:
                ext_file = os.path.splitext(secure_filename(f_file.filename))[1].lower() or '.jpg'
                fname = f'extend_{booking_id}_{uuid.uuid4().hex[:8]}{ext_file}'
                upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                f_file.save(os.path.join(upload_dir, fname))
                base_url = 'https://autoride-booking-system.vercel.app/api/uploads'
                payment_proof_url = f'{base_url}/{fname}'

        # 4. Calculate extension days
        from datetime import datetime as _dt
        orig_end = booking['end_date']
        if isinstance(orig_end, str):
            orig_end = _dt.strptime(orig_end.split('T')[0], '%Y-%m-%d').date()
        new_end_obj = _dt.strptime(new_end_date.split('T')[0], '%Y-%m-%d').date()
        ext_days = (new_end_obj - orig_end).days
        if ext_days <= 0:
            return jsonify({"error": "New end date must be after current end date"}), 400

        # 5. Insert extension request
        cur.execute("""
            INSERT INTO booking_extensions
                (booking_id, requested_by, original_end_date, new_end_date,
                 extension_days, extension_price, payment_method, reference_number,
                 payment_proof_url, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
            RETURNING id
        """, (
            booking_id, booking['user_id'], orig_end, new_end_date,
            ext_days, float(extension_price), payment_method,
            reference_number or None, payment_proof_url
        ))
        ext_id = cur.fetchone()['id']
        commit_db()

        # 6. Notify admins
        try:
            from notifications import notification_service
            notification_service.notify_admins_inapp(
                "Extension Request",
                f"Booking #{booking_id} — customer requests {ext_days}-day extension until {new_end_date}. PHP {float(extension_price):,.2f} paid via {payment_method}.",
                'admin_extension_request'
            )
        except Exception:
            pass

        return jsonify({
            "message": "Extension request submitted. Awaiting admin approval.",
            "extension_id": ext_id,
            "extension_days": ext_days,
            "new_end_date": new_end_date,
            "status": "pending"
        }), 200

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/bookings/<int:booking_id>/extensions', methods=['GET'])
def get_booking_extensions(booking_id):
    """Get all extension requests for a booking."""
    try:
        cur = get_cursor()
        cur.execute("""
            SELECT * FROM booking_extensions WHERE booking_id = %s
            ORDER BY created_at DESC
        """, (booking_id,))
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            for k in ('original_end_date', 'new_end_date', 'created_at', 'updated_at'):
                if d.get(k): d[k] = str(d[k]).split('T')[0] if 'T' in str(d[k]) else str(d[k])
            result.append(d)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/extensions/<int:ext_id>/approve', methods=['PUT'])
def approve_extension(ext_id):
    """Admin approves an extension request — updates booking end_date."""
    try:
        cur = get_cursor()
        cur.execute("SELECT * FROM booking_extensions WHERE id = %s", (ext_id,))
        ext = cur.fetchone()
        if not ext:
            return jsonify({"error": "Extension not found"}), 404

        # Update extension status
        cur.execute("""
            UPDATE booking_extensions SET status = 'approved', updated_at = NOW()
            WHERE id = %s
        """, (ext_id,))

        # Update booking end_date and add to total_price
        cur.execute("""
            UPDATE bookings
            SET end_date = %s,
                total_price = total_price + %s
            WHERE id = %s
        """, (ext['new_end_date'], ext['extension_price'], ext['booking_id']))

        commit_db()

        # Notify customer
        try:
            from notifications import notification_service
            cur.execute("SELECT user_id FROM bookings WHERE id = %s", (ext['booking_id'],))
            b = cur.fetchone()
            if b:
                notification_service.notify_user(
                    b['user_id'],
                    "Extension Approved",
                    f"Your extension for Booking #{ext['booking_id']} has been approved! New return date: {ext['new_end_date']}.",
                    'extension_approved'
                )
        except Exception:
            pass

        return jsonify({"message": "Extension approved", "new_end_date": str(ext['new_end_date'])}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/extensions/<int:ext_id>/reject', methods=['PUT'])
def reject_extension(ext_id):
    """Admin rejects extension — notes refund-upon-return."""
    try:
        data = request.get_json() or {}
        note = data.get('note', 'Extension rejected by admin. Refund will be processed upon vehicle return.')
        cur = get_cursor()
        cur.execute("""
            UPDATE booking_extensions
            SET status = 'rejected', admin_note = %s, updated_at = NOW()
            WHERE id = %s
        """, (note, ext_id))
        cur.execute("SELECT booking_id, extension_price, requested_by FROM booking_extensions WHERE id = %s", (ext_id,))
        ext = cur.fetchone()
        commit_db()

        # Notify customer
        try:
            from notifications import notification_service
            if ext:
                notification_service.notify_user(
                    ext['requested_by'],
                    "Extension Request Rejected",
                    f"Your extension request for Booking #{ext['booking_id']} was not approved. Your payment of PHP {float(ext['extension_price']):,.2f} will be refunded upon vehicle return.",
                    'extension_rejected'
                )
        except Exception:
            pass

        return jsonify({"message": "Extension rejected. Refund noted for upon-return processing."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/extensions', methods=['GET'])
def get_all_extensions():
    """Admin: get all pending extension requests."""
    try:
        cur = get_cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS booking_extensions (
                id BIGSERIAL PRIMARY KEY, booking_id INTEGER,
                requested_by INTEGER, original_end_date DATE, new_end_date DATE,
                extension_days INTEGER, extension_price NUMERIC(12,2),
                payment_method VARCHAR(100), reference_number VARCHAR(200),
                payment_proof_url TEXT, status VARCHAR(20) DEFAULT 'pending',
                admin_note TEXT, created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            SELECT e.*, b.status as booking_status, u.full_name as customer_name,
                   CONCAT(v.brand, ' ', v.model, ' (', v.plate_number, ')') as car
            FROM booking_extensions e
            JOIN bookings b ON b.id = e.booking_id
            JOIN users u ON u.id = e.requested_by
            JOIN vehicles v ON v.id = b.vehicle_id
            WHERE e.status = 'pending'
            ORDER BY e.created_at DESC
        """)
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            for k in ('original_end_date','new_end_date','created_at','updated_at'):
                if d.get(k): d[k] = str(d[k]).split('T')[0] if 'T' in str(d[k]) else str(d[k])
            result.append(d)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


'''

if idx >= 0:
    app_content = app_content[:idx] + extend_endpoint + app_content[idx:]
    with open('backend/app.py', 'wb') as f:
        f.write(app_content.encode('utf-8'))
    print('Step 1 done: Backend endpoints added')
else:
    print('Step 1 ERROR: insertion point not found')

print('Backend done.')
