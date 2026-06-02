"""
Booking Extension Routes
Handles extend booking requests, admin approval/rejection.
"""
from flask import Blueprint, request, jsonify
from database import get_cursor, commit_db
import os
import uuid
from datetime import datetime as _dt

ext_bp = Blueprint('extensions', __name__)


def _ensure_extensions_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS booking_extensions (
            id                BIGSERIAL PRIMARY KEY,
            booking_id        INTEGER NOT NULL,
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


@ext_bp.route('/bookings/<int:booking_id>/extend', methods=['POST'])
def extend_booking(booking_id):
    try:
        data = request.form if request.files else (request.get_json() or {})
        new_end_date    = (data.get('new_end_date') or '').strip()
        extension_price = data.get('extension_price')
        payment_method  = data.get('payment_method', 'Cash (Over the counter)')
        reference_number= data.get('reference_number', '')

        if not new_end_date or not extension_price:
            return jsonify({"error": "new_end_date and extension_price are required"}), 400

        cur = get_cursor()
        _ensure_extensions_table(cur)

        cur.execute("SELECT id, user_id, end_date, status FROM bookings WHERE id = %s", (booking_id,))
        booking = cur.fetchone()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        if booking['status'] not in ('Picked Up', 'Ongoing', 'Confirmed', 'Approved'):
            return jsonify({"error": "Booking cannot be extended in its current status"}), 400

        # Handle payment proof upload
        payment_proof_url = None
        if 'payment_proof' in request.files:
            from werkzeug.utils import secure_filename
            f_file = request.files['payment_proof']
            if f_file and f_file.filename:
                ext_file = os.path.splitext(secure_filename(f_file.filename))[1].lower() or '.jpg'
                fname = 'extend_' + str(booking_id) + '_' + uuid.uuid4().hex[:8] + ext_file
                upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                f_file.save(os.path.join(upload_dir, fname))
                payment_proof_url = 'https://autoride-booking-system.vercel.app/api/uploads/' + fname

        # Calculate extension days
        orig_end = booking['end_date']
        if isinstance(orig_end, str):
            orig_end = _dt.strptime(orig_end.split('T')[0], '%Y-%m-%d').date()
        new_end_obj = _dt.strptime(new_end_date.split('T')[0], '%Y-%m-%d').date()
        ext_days = (new_end_obj - orig_end).days
        if ext_days <= 0:
            return jsonify({"error": "New end date must be after current end date"}), 400

        cur.execute("""
            INSERT INTO booking_extensions
                (booking_id, requested_by, original_end_date, new_end_date,
                 extension_days, extension_price, payment_method, reference_number,
                 payment_proof_url, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
            RETURNING id
        """, (booking_id, booking['user_id'], orig_end, new_end_date,
              ext_days, float(extension_price), payment_method,
              reference_number or None, payment_proof_url))
        ext_id = cur.fetchone()['id']
        commit_db()

        try:
            from notifications import notification_service
            notification_service.notify_admins_inapp(
                "Extension Request",
                "Booking #" + str(booking_id) + " - " + str(ext_days) + "-day extension requested. PHP " + str(float(extension_price)) + " via " + str(payment_method) + ".",
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


@ext_bp.route('/bookings/<int:booking_id>/extensions', methods=['GET'])
def get_booking_extensions(booking_id):
    try:
        cur = get_cursor()
        _ensure_extensions_table(cur)
        cur.execute("SELECT * FROM booking_extensions WHERE booking_id = %s ORDER BY created_at DESC", (booking_id,))
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            for k in ('original_end_date', 'new_end_date', 'created_at', 'updated_at'):
                if d.get(k): d[k] = str(d[k]).split('T')[0] if 'T' in str(d.get(k,'')) else str(d[k])
            result.append(d)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ext_bp.route('/admin/extensions', methods=['GET'])
def get_all_extensions():
    try:
        cur = get_cursor()
        _ensure_extensions_table(cur)
        cur.execute("""
            SELECT e.id, e.booking_id, e.extension_days, e.extension_price,
                   e.payment_method, e.reference_number, e.payment_proof_url,
                   e.status, e.created_at, e.new_end_date, e.original_end_date,
                   u.full_name as customer_name,
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
            for k in ('original_end_date', 'new_end_date', 'created_at', 'updated_at'):
                if d.get(k): d[k] = str(d[k]).split('T')[0] if 'T' in str(d.get(k,'')) else str(d[k])
            result.append(d)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ext_bp.route('/admin/extensions/<int:ext_id>/approve', methods=['PUT'])
def approve_extension(ext_id):
    try:
        cur = get_cursor()
        cur.execute("SELECT * FROM booking_extensions WHERE id = %s", (ext_id,))
        ext = cur.fetchone()
        if not ext:
            return jsonify({"error": "Extension not found"}), 404
        cur.execute("UPDATE booking_extensions SET status = 'approved', updated_at = NOW() WHERE id = %s", (ext_id,))
        cur.execute("UPDATE bookings SET end_date = %s, total_price = total_price + %s WHERE id = %s",
                    (ext['new_end_date'], ext['extension_price'], ext['booking_id']))
        commit_db()
        try:
            from notifications import notification_service
            cur.execute("SELECT user_id FROM bookings WHERE id = %s", (ext['booking_id'],))
            b = cur.fetchone()
            if b:
                notification_service.notify_user(b['user_id'], "Extension Approved",
                    "Your extension for Booking #" + str(ext['booking_id']) + " was approved! New return: " + str(ext['new_end_date']) + ".",
                    'extension_approved')
        except Exception:
            pass
        return jsonify({"message": "Extension approved", "new_end_date": str(ext['new_end_date'])}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ext_bp.route('/admin/extensions/<int:ext_id>/reject', methods=['PUT'])
def reject_extension(ext_id):
    try:
        data = request.get_json() or {}
        note = data.get('note', 'Extension rejected. Refund will be processed upon vehicle return.')
        cur = get_cursor()
        cur.execute("SELECT * FROM booking_extensions WHERE id = %s", (ext_id,))
        ext = cur.fetchone()
        if not ext:
            return jsonify({"error": "Extension not found"}), 404
        cur.execute("UPDATE booking_extensions SET status = 'rejected', admin_note = %s, updated_at = NOW() WHERE id = %s",
                    (note, ext_id))
        commit_db()
        try:
            from notifications import notification_service
            notification_service.notify_user(ext['requested_by'], "Extension Rejected",
                "Your extension for Booking #" + str(ext['booking_id']) + " was not approved. PHP " + str(float(ext['extension_price'])) + " will be refunded upon return.",
                'extension_rejected')
        except Exception:
            pass
        return jsonify({"message": "Extension rejected. Refund noted."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
