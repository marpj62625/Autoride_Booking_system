"""
Booking Extension Routes
Handles extend booking requests, admin approval/rejection.
"""
from flask import Blueprint, request, jsonify
from database import get_cursor, commit_db
import os
import uuid
from datetime import datetime as _dt

try:
    from notifications import notification_service
except Exception as _nse:
    class DummyNotificationService:
        def notify_user(self, *args, **kwargs): return True
        def notify_admins_inapp(self, *args, **kwargs): return []
    notification_service = DummyNotificationService()

ext_bp = Blueprint('extensions', __name__)


# ─── EXTENSION PAYMENT RECORDING & RECEIPTS ──────────────────────────────────

def _ensure_payment_ext_columns(cur):
    """Idempotently add extension tracking columns to payments table."""
    cur.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS extension_id INTEGER")
    cur.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()")


def _record_extension_payment(cur, ext):
    """
    Records the extension fee as a payment and adds it to the booking's amount_paid.
    Idempotent: does nothing if this extension already has a payment row.
    Returns True if a new payment was recorded.
    """
    ext_id = ext['id']
    cur.execute("SELECT id FROM payments WHERE extension_id = %s LIMIT 1", (ext_id,))
    if cur.fetchone():
        return False
    price = float(ext.get('extension_price') or 0)
    ref = ext.get('reference_number') or f"EXT-{ext_id}"
    cur.execute("""
        INSERT INTO payments (booking_id, amount, method, reference_number, payment_proof, status, extension_id, created_at)
        VALUES (%s, %s, %s, %s, %s, 'Completed', %s, COALESCE(%s, NOW()))
    """, (ext['booking_id'], price, ext.get('payment_method') or 'Online', str(ref),
          ext.get('payment_proof_url'), ext_id, ext.get('approved_at') or ext.get('created_at')))
    cur.execute("""
        UPDATE bookings
        SET amount_paid = COALESCE(amount_paid, 0) + %s
        WHERE id = %s
    """, (price, ext['booking_id']))
    return True


def _backfill_extension_payments(cur, booking_id=None):
    """Records missing payments for already-approved extensions (fixes amount_paid mismatch)."""
    _ensure_payment_ext_columns(cur)
    q = """
        SELECT e.* FROM booking_extensions e
        WHERE e.status = 'approved'
          AND NOT EXISTS (SELECT 1 FROM payments p WHERE p.extension_id = e.id)
    """
    params = ()
    if booking_id:
        q += " AND e.booking_id = %s"
        params = (booking_id,)
    cur.execute(q, params)
    rows = cur.fetchall() or []
    count = 0
    for r in rows:
        if _record_extension_payment(cur, dict(r)):
            count += 1
    return count


_GLOBAL_EXT_BACKFILL_DONE = {'done': False}

@ext_bp.before_app_request
def _run_global_extension_backfill_once():
    if _GLOBAL_EXT_BACKFILL_DONE['done']:
        return
    _GLOBAL_EXT_BACKFILL_DONE['done'] = True
    try:
        cur = get_cursor()
        _ensure_extensions_table(cur)
        n = _backfill_extension_payments(cur)
        commit_db()
        if n:
            print(f"[Extensions] Backfilled {n} missing extension payment(s)")
    except Exception as _bf_err:
        print(f"[Extensions] Global backfill skipped: {_bf_err}")
        try:
            from database import get_db
            get_db().rollback()
        except Exception:
            pass


def _send_extension_receipt_email(ext_id):
    """Sends a separate extension receipt email to the renter."""
    try:
        cur = get_cursor()
        cur.execute("""
            SELECT e.id AS ext_id, e.booking_id, e.extension_days, e.extension_price, e.payment_method,
                   e.reference_number, e.original_end_date, e.new_end_date, e.approved_at, e.created_at,
                   b.total_price, b.amount_paid, b.balance_amount, b.start_date,
                   u.full_name, u.email, v.brand, v.model, v.plate_number, v.daily_rate
            FROM booking_extensions e
            JOIN bookings b ON b.id = e.booking_id
            JOIN users u ON u.id = b.user_id
            LEFT JOIN vehicles v ON v.id = b.vehicle_id
            WHERE e.id = %s
        """, (ext_id,))
        d = cur.fetchone()
        if not d or not d.get('email'):
            return
        from app import send_email_notifications
        bid = str(d['booking_id'])
        price = float(d.get('extension_price') or 0)
        receipt_url = f"https://autoride-booking-system.vercel.app/api/bookings/{bid}/receipt?extension_id={d['ext_id']}"
        from datetime import datetime as _d2
        now_str = _d2.now().strftime("%Y-%m-%d %H:%M:%S")

        def row(label, val):
            return f"<tr><td style='padding:3px 0;'>{label}</td><td style='text-align:right;padding:3px 0;'>{val}</td></tr>"

        html = (
            "<body style='margin:0;padding:20px;background:#f0f0f0;font-family:Arial,sans-serif;'>"
            "<div style='max-width:380px;margin:0 auto;background:#fff;padding:20px;color:#000;box-shadow:0 2px 10px rgba(0,0,0,0.1);'>"
            "<div style='text-align:center;margin-bottom:15px;'>"
            "<h2 style='margin:0;font-size:22px;letter-spacing:1px;text-transform:uppercase;'>AUTORIDE</h2>"
            "<p style='margin:2px 0 0;font-size:12px;'>Your ride, your way</p></div>"
            "<div style='text-align:center;font-weight:bold;font-size:16px;margin:15px 0;border-top:1px dashed #000;border-bottom:1px dashed #000;padding:8px 0;letter-spacing:2px;'>EXTENSION RECEIPT</div>"
            "<table width='100%' style='font-size:13px;margin-bottom:15px;line-height:1.4;'>"
            + row('Booking No', bid)
            + row('Extension No', f"EXT-{d['ext_id']}")
            + row('Date', now_str)
            + row('Customer', str(d.get('full_name') or 'Customer'))
            + row('Vehicle', f"{d.get('brand') or ''} {d.get('model') or ''}")
            + row('Previous Return', str(d.get('original_end_date')))
            + row('New Return', str(d.get('new_end_date')))
            + "</table><div style='border-top:1px dashed #000;margin:10px 0;'></div>"
            "<table width='100%' style='font-size:13px;margin-bottom:10px;'>"
            + row(f"Rental Extension ({d.get('extension_days')} day{'s' if int(d.get('extension_days') or 0) != 1 else ''})", '{:,.2f}'.format(max(price, round(float(d.get('daily_rate') or 0) * int(d.get('extension_days') or 0), 2))))
            + (row('Discount Applied', '-' + '{:,.2f}'.format(round(float(d.get('daily_rate') or 0) * int(d.get('extension_days') or 0) - price, 2))) if (float(d.get('daily_rate') or 0) * int(d.get('extension_days') or 0) - price) > 0.01 else '')
            + "</table><div style='border-top:1px dashed #000;margin:10px 0;'></div>"
            "<table width='100%' style='font-size:14px;margin-bottom:15px;'>"
            f"<tr><td><strong>AMOUNT PAID (PHP)</strong></td><td style='text-align:right;'><strong>{'{:,.2f}'.format(price)}</strong></td></tr>"
            + row('Updated Contract Total', '{:,.2f}'.format(float(d.get('total_price') or 0)))
            + row('Total Paid to Date', '{:,.2f}'.format(float(d.get('amount_paid') or 0)))
            + "</table><div style='border-top:1px dashed #000;margin:10px 0;'></div>"
            "<table width='100%' style='font-size:13px;margin-bottom:20px;'>"
            + row('Payment Method', str(d.get('payment_method') or 'N/A'))
            + row('Reference No', str(d.get('reference_number') or f"EXT-{d['ext_id']}"))
            + "</table>"
            "<div style='text-align:center;margin-top:20px;'>"
            f"<a href='{receipt_url}' style='display:inline-block;border:1px solid #000;color:#000;text-decoration:none;padding:8px 15px;font-size:12px;text-transform:uppercase;'>Download PDF</a>"
            "</div></div></body>"
        )
        send_email_notifications(d['email'], f"Autoride Extension Receipt - Booking #{bid}", html, is_html=True)
        print(f"[Extensions] Extension receipt email sent to {d['email']} for EXT-{d['ext_id']}")
    except Exception as _em_err:
        print(f"[Extensions] Extension receipt email error: {_em_err}")


@ext_bp.route('/bookings/<int:booking_id>/receipts', methods=['GET'])
@ext_bp.route('/api/bookings/<int:booking_id>/receipts', methods=['GET'])
def list_booking_receipts(booking_id):
    """Returns all separate receipts of a booking: original booking + each approved extension."""
    try:
        cur = get_cursor()
        _ensure_extensions_table(cur)
        if _backfill_extension_payments(cur, booking_id):
            commit_db()
        cur.execute("""
            SELECT b.*, v.brand, v.model, v.plate_number, v.daily_rate
            FROM bookings b LEFT JOIN vehicles v ON v.id = b.vehicle_id
            WHERE b.id = %s
        """, (booking_id,))
        b = cur.fetchone()
        if not b:
            return jsonify({"error": "Booking not found"}), 404
        b = dict(b)

        cur.execute("""
            SELECT e.*, p.id AS payment_id, p.method AS pay_method, p.reference_number AS pay_ref
            FROM booking_extensions e
            LEFT JOIN payments p ON p.extension_id = e.id
            WHERE e.booking_id = %s AND e.status = 'approved'
            ORDER BY e.created_at ASC, e.id ASC
        """, (booking_id,))
        exts = [dict(r) for r in (cur.fetchall() or [])]

        cur.execute("""
            SELECT method, reference_number, created_at FROM payments
            WHERE booking_id = %s AND extension_id IS NULL
            ORDER BY id DESC LIMIT 1
        """, (booking_id,))
        main_pay = cur.fetchone()
        main_pay = dict(main_pay) if main_pay else {}

        ext_total = sum(float(e.get('extension_price') or 0) for e in exts)
        orig_total = max(0.0, float(b.get('total_price') or 0) - ext_total)
        orig_paid = max(0.0, float(b.get('amount_paid') or 0) - ext_total)
        orig_end = exts[0]['original_end_date'] if exts else b.get('end_date')

        def s(v):
            return str(v) if v is not None else ''

        # Calculate days for original booking
        orig_days = 1
        try:
            if b.get('start_date') and orig_end:
                import datetime
                d1 = b['start_date'] if isinstance(b['start_date'], (datetime.date, datetime.datetime)) else datetime.datetime.strptime(str(b['start_date'])[:10], '%Y-%m-%d').date()
                d2 = orig_end if isinstance(orig_end, (datetime.date, datetime.datetime)) else datetime.datetime.strptime(str(orig_end)[:10], '%Y-%m-%d').date()
                orig_days = max(1, (d2 - d1).days)
        except Exception:
            orig_days = 1

        daily_rate_val = float(b.get('daily_rate') or 0)
        base_price_val = float(b.get('base_price') or 0)
        if base_price_val <= 0 and daily_rate_val > 0:
            base_price_val = round(daily_rate_val * orig_days, 2)
        elif daily_rate_val <= 0 and base_price_val > 0 and orig_days > 0:
            daily_rate_val = round(base_price_val / orig_days, 2)

        addon_price_val = float(b.get('addon_price') or 0)
        ins_price_val = float(b.get('insurance_price') or 0)
        driver_fee_val = float(b.get('driver_fee') or 0)
        delivery_fee_val = float(b.get('delivery_fee') or 0)
        payment_fee_val = float(b.get('payment_fee') or 0)
        discount_val = float(b.get('discount_amount') or 0)
        pts_val = float(b.get('points_discount_amount') or b.get('points_redeemed') or 0)

        # Fallback discount detection if not explicitly recorded
        calc_subtotal = base_price_val + addon_price_val + ins_price_val + driver_fee_val + delivery_fee_val + payment_fee_val
        if discount_val <= 0 and (calc_subtotal - pts_val) > (orig_total + 0.05):
            discount_val = round((calc_subtotal - pts_val) - orig_total, 2)

        receipts = [{
            'key': 'booking',
            'type': 'booking',
            'extension_id': None,
            'label': 'Original Booking Receipt',
            'receipt_no': str(booking_id).zfill(6),
            'amount': round(orig_paid, 2),
            'total': round(orig_total, 2),
            'method': main_pay.get('method') or b.get('payment_method') or b.get('payment_type') or 'N/A',
            'reference_number': main_pay.get('reference_number') or b.get('reference_number') or '',
            'date': s(main_pay.get('created_at') or b.get('created_at')),
            'start_date': s(b.get('start_date')),
            'end_date': s(orig_end),
            'days': orig_days,
            'daily_rate': daily_rate_val,
            'base_price': base_price_val,
            'addon_price': addon_price_val,
            'insurance_type': b.get('insurance_type') or 'Basic Protection',
            'insurance_price': ins_price_val,
            'driver_fee': driver_fee_val,
            'delivery_fee': delivery_fee_val,
            'payment_fee': payment_fee_val,
            'discount_amount': discount_val,
            'points_discount_amount': pts_val,
        }]
        for idx, e in enumerate(exts, start=1):
            e_days = int(e.get('extension_days') or 1)
            e_base = round(float(b.get('daily_rate') or daily_rate_val) * e_days, 2)
            e_price = float(e.get('extension_price') or 0)
            e_disc = max(0.0, round(e_base - e_price, 2))
            receipts.append({
                'key': f"ext-{e['id']}",
                'type': 'extension',
                'extension_id': e['id'],
                'label': f"Extension #{idx} Receipt (+{e_days} day{'s' if e_days != 1 else ''})",
                'receipt_no': f"{str(booking_id).zfill(6)}-E{idx}",
                'amount': e_price,
                'total': e_price,
                'extension_days': e_days,
                'days': e_days,
                'daily_rate': float(b.get('daily_rate') or daily_rate_val),
                'method': e.get('pay_method') or e.get('payment_method') or 'N/A',
                'reference_number': e.get('pay_ref') or e.get('reference_number') or f"EXT-{e['id']}",
                'date': s(e.get('approved_at') or e.get('created_at')),
                'start_date': s(e.get('original_end_date')),
                'end_date': s(e.get('new_end_date')),
                'base_price': e_base,
                'discount_amount': e_disc,
            })
        return jsonify({
            'booking_id': booking_id,
            'brand': b.get('brand'), 'model': b.get('model'), 'plate_number': b.get('plate_number'),
            'rental_type': b.get('rental_type'), 'insurance_type': b.get('insurance_type') or 'Basic Protection',
            'insurance_price': ins_price_val,
            'addons': b.get('addons'),
            'base_price': base_price_val,
            'addon_price': addon_price_val,
            'driver_fee': driver_fee_val,
            'delivery_fee': delivery_fee_val,
            'payment_fee': payment_fee_val,
            'total_price': float(b.get('total_price') or 0),
            'amount_paid': float(b.get('amount_paid') or 0),
            'balance_amount': float(b.get('balance_amount') or 0),
            'discount_amount': discount_val,
            'points_discount_amount': pts_val,
            'daily_rate': daily_rate_val,
            'days': orig_days,
            'receipts': receipts
        }), 200
    except Exception as e:
        import traceback; traceback.print_exc()
        try:
            from database import get_db
            get_db().rollback()
        except Exception:
            pass
        return jsonify({"error": str(e)}), 500


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
        # Accept both multipart/form-data (with or without file upload) and application/json
        ct = request.content_type or ''
        if 'multipart/form-data' in ct or 'application/x-www-form-urlencoded' in ct:
            data = request.form
        else:
            data = request.get_json(silent=True) or {}

        new_end_date    = (data.get('new_end_date') or '').strip()
        extension_price = data.get('extension_price')
        payment_method  = data.get('payment_method', 'Cash (Over the counter)')
        reference_number= data.get('reference_number', '')

        if not new_end_date or not extension_price:
            return jsonify({"error": "new_end_date and extension_price are required"}), 400

        # Normalise new_end_date to YYYY-MM-DD regardless of input format
        import re
        if re.match(r'^\d{4}-\d{2}-\d{2}$', new_end_date):
            pass  # already good
        elif 'T' in new_end_date:
            new_end_date = new_end_date.split('T')[0]

        cur = get_cursor()
        _ensure_extensions_table(cur)
        commit_db()  # commit DDL so table exists before INSERT

        cur = get_cursor()
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

        # Calculate extension days - handle date object, datetime, or string
        import datetime as _datetime_mod
        orig_end = booking['end_date']
        if isinstance(orig_end, _datetime_mod.datetime):
            orig_end = orig_end.date()
        elif isinstance(orig_end, str):
            orig_end = _datetime_mod.datetime.strptime(orig_end[:10], '%Y-%m-%d').date()
        # else already a date object from psycopg2

        new_end_obj = _datetime_mod.datetime.strptime(new_end_date, '%Y-%m-%d').date()
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
@ext_bp.route('/api/bookings/<int:booking_id>/extensions', methods=['GET'])
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
@ext_bp.route('/api/admin/extensions', methods=['GET'])
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
@ext_bp.route('/api/admin/extensions/<int:ext_id>/approve', methods=['PUT'])
def approve_extension(ext_id):
    try:
        cur = get_cursor()

        # Ensure required tables and columns exist (idempotent migration guard)
        try:
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
            cur.execute("ALTER TABLE booking_extensions ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ")
            cur.execute("ALTER TABLE booking_extensions ADD COLUMN IF NOT EXISTS has_conflicts BOOLEAN DEFAULT FALSE")
            cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS has_active_extension BOOLEAN DEFAULT FALSE")
            cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS extension_count INT DEFAULT 0")
            cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS is_conflict_affected BOOLEAN DEFAULT FALSE")
            cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS conflict_id INT DEFAULT NULL")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS booking_conflicts (
                    id                              BIGSERIAL PRIMARY KEY,
                    extension_id                    INTEGER NOT NULL,
                    affected_booking_id             INTEGER NOT NULL,
                    affected_user_id                INTEGER NOT NULL,
                    conflict_start_date             DATE,
                    conflict_end_date               DATE,
                    resolution_status               VARCHAR(50) DEFAULT 'Pending',
                    resolution_deadline             TIMESTAMPTZ,
                    selected_alternative_vehicle_id INTEGER,
                    refund_amount                   NUMERIC(12,2),
                    refund_status                   VARCHAR(50) DEFAULT 'Pending',
                    refund_transaction_id           VARCHAR(200),
                    customer_notified_at            TIMESTAMPTZ,
                    customer_responded_at           TIMESTAMPTZ,
                    created_at                      TIMESTAMPTZ DEFAULT NOW(),
                    updated_at                      TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            commit_db()
        except Exception as schema_err:
            print(f"DEBUG approve_extension: schema guard error (non-fatal): {schema_err}")
            # Re-get cursor after possible error
            cur = get_cursor()

        cur.execute("SELECT * FROM booking_extensions WHERE id = %s", (ext_id,))
        ext = cur.fetchone()
        if not ext:
            return jsonify({"error": "Extension not found"}), 404
            
        import datetime
        from services.extension_service import detect_conflicts
        
        # Detect overlaps
        print(f"DEBUG approve_extension: Checking conflicts for booking {ext['booking_id']} with new_end_date {ext['new_end_date']}")
        conflicts = detect_conflicts(ext['booking_id'], ext['new_end_date'])
        has_conflicts = len(conflicts) > 0
        print(f"DEBUG approve_extension: Found {len(conflicts)} conflicts")
        
        cur.execute("""
            UPDATE booking_extensions 
            SET status = 'approved', has_conflicts = %s, approved_at = NOW(), updated_at = NOW() 
            WHERE id = %s
        """, (has_conflicts, ext_id))
        
        cur.execute("""
            UPDATE bookings 
            SET end_date = %s, total_price = total_price + %s, has_active_extension = TRUE, extension_count = COALESCE(extension_count, 0) + 1 
            WHERE id = %s
        """, (ext['new_end_date'], ext['extension_price'], ext['booking_id']))

        # Record the extension fee as a separate payment and update amount_paid
        try:
            _ensure_payment_ext_columns(cur)
            _record_extension_payment(cur, dict(ext))
        except Exception as _rp_err:
            print(f"DEBUG approve_extension: record payment error: {_rp_err}")
        
        # Get dynamic deadline hours setting
        cur.execute("SELECT value FROM settings WHERE key = 'extension_conflict_deadline_hours'")
        setting_row = cur.fetchone()
        deadline_hours = int(setting_row['value']) if setting_row else 72

        # Process each conflict
        for conf_booking in conflicts:
            deadline = _dt.now() + datetime.timedelta(hours=deadline_hours)
            print(f"DEBUG approve_extension: Creating conflict record for booking {conf_booking['id']}, user {conf_booking['user_id']}")
            cur.execute("""
                INSERT INTO booking_conflicts 
                    (extension_id, affected_booking_id, affected_user_id, conflict_start_date, conflict_end_date, resolution_status, resolution_deadline)
                VALUES (%s, %s, %s, %s, %s, 'Pending', %s)
                RETURNING id
            """, (ext_id, conf_booking['id'], conf_booking['user_id'], conf_booking['start_date'], conf_booking['end_date'], deadline))
            conflict_rec_id = cur.fetchone()['id']
            print(f"DEBUG approve_extension: Created booking_conflict record id={conflict_rec_id}")
            
            cur.execute("""
                UPDATE bookings 
                SET is_conflict_affected = TRUE, conflict_id = %s 
                WHERE id = %s
            """, (conflict_rec_id, conf_booking['id']))
            
            try:
                from notifications import notification_service
                notification_service.notify_user(
                    conf_booking['user_id'],
                    "Booking Conflict Alert",
                    f"Your booking #{conf_booking['id']} has a conflict because the current renter extended their trip. Please choose an alternative vehicle or request a full refund within {deadline_hours} hours.",
                    'booking_conflict'
                )
                print(f"DEBUG approve_extension: Notified user {conf_booking['user_id']} of conflict")
            except Exception as notify_err:
                print(f"DEBUG approve_extension: Notification failed (non-fatal): {notify_err}")
                
        commit_db()
        _send_extension_receipt_email(ext_id)
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
        return jsonify({"message": "Extension approved", "new_end_date": str(ext['new_end_date']), "has_conflicts": has_conflicts, "conflicts_found": len(conflicts)}), 200
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@ext_bp.route('/admin/extensions/<int:ext_id>/reject', methods=['PUT'])
@ext_bp.route('/api/admin/extensions/<int:ext_id>/reject', methods=['PUT'])
def reject_extension(ext_id):
    try:
        data = request.get_json(silent=True) or {}
        note = data.get('note', 'Extension rejected. Refund will be processed.')
        cur = get_cursor()
        cur.execute("SELECT * FROM booking_extensions WHERE id = %s", (ext_id,))
        ext = cur.fetchone()
        if not ext:
            return jsonify({"error": "Extension not found"}), 404
        cur.execute("UPDATE booking_extensions SET status = 'rejected', admin_note = %s, updated_at = NOW() WHERE id = %s",
                    (note, ext_id))

        # Mark booking as Refund Pending so admin can process the refund
        cur.execute("""
            UPDATE bookings
            SET payment_status = 'Refund Pending'
            WHERE id = %s AND payment_status NOT IN ('Refunded', 'Unpaid')
        """, (ext['booking_id'],))

        commit_db()
        try:
            from notifications import notification_service
            notification_service.notify_user(ext['requested_by'], "Extension Rejected",
                f"Your extension request for Booking #{ext['booking_id']} was not approved. "
                f"A refund of PHP {float(ext['extension_price']):,.2f} will be processed by our team.",
                'extension_rejected')
        except Exception:
            pass
        return jsonify({
            "message": "Extension rejected. Booking marked for refund.",
            "refund_amount": float(ext['extension_price']),
            "booking_id": ext['booking_id'],
            "extension_id": ext_id
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
