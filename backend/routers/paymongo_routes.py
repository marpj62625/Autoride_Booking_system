"""
PayMongo Payment Integration Routes
Supports: GCash, Maya, Credit/Debit Card
Flow: Create payment link -> Redirect user -> Webhook confirms payment
"""
import base64
import hashlib
import hmac
import json
import requests
from flask import Blueprint, request, jsonify
from database import get_cursor, commit_db, get_db
from config import PAYMONGO_SECRET_KEY, PAYMONGO_PUBLIC_KEY, PAYMONGO_WEBHOOK_SECRET, APP_BASE_URL

paymongo_bp = Blueprint('paymongo', __name__)

PAYMONGO_API = 'https://api.paymongo.com/v1'

def get_auth_header():
    """Base64 encode the secret key for PayMongo Basic Auth."""
    encoded = base64.b64encode(f'{PAYMONGO_SECRET_KEY}:'.encode()).decode()
    return {'Authorization': f'Basic {encoded}', 'Content-Type': 'application/json'}


# ??? CREATE PAYMENT LINK ????????????????????????????????????????????????????

@paymongo_bp.route('/paymongo/create-payment', methods=['POST'])
@paymongo_bp.route('/api/paymongo/create-payment', methods=['POST'])
def create_payment():
    """
    Create a PayMongo payment link for GCash, Maya, or Card.
    Returns a checkout_url to redirect the user to.
    """
    data = request.get_json(silent=True) or {}
    booking_id = data.get('booking_id')
    amount = data.get('amount')          # in PHP (e.g. 2500.00)
    method = data.get('method')          # 'gcash', 'paymaya', 'card'
    description = data.get('description', f'Autoride Booking #{booking_id}')
    customer_name = data.get('customer_name', '')
    customer_email = data.get('customer_email', '')
    customer_phone = data.get('customer_phone', '')
    payment_type = data.get('payment_type', 'Full')

    # Log incoming request for debugging
    print(f"[PayMongo] Create payment request: booking_id={booking_id}, amount={amount}, method={method}")

    if not all([booking_id, amount, method]):
        missing_fields = []
        if not booking_id:
            missing_fields.append('booking_id')
        if not amount:
            missing_fields.append('amount')
        if not method:
            missing_fields.append('method')
        error_msg = f'Missing required fields: {", ".join(missing_fields)}'
        print(f"[PayMongo] Error: {error_msg}")
        return jsonify({'error': error_msg}), 400

    # PayMongo amounts are in centavos (multiply by 100)
    try:
        amount_centavos = int(float(amount) * 100)
    except (ValueError, TypeError) as e:
        error_msg = f'Invalid amount format: {amount}'
        print(f"[PayMongo] Error: {error_msg}")
        return jsonify({'error': error_msg}), 400

    if amount_centavos < 10000:  # Minimum 100 PHP
        error_msg = 'Minimum payment amount is PHP 100'
        print(f"[PayMongo] Error: {error_msg} (amount_centavos={amount_centavos})")
        return jsonify({'error': error_msg}), 400

    # Map method names to PayMongo payment method types
    method_map = {
        'gcash': 'gcash',
        'maya': 'paymaya',
        'paymaya': 'paymaya',
        'card': 'card',
        'credit_card': 'card',
        'debit_card': 'card',
    }
    pm_type = method_map.get(method.lower())
    if not pm_type:
        error_msg = f'Unsupported payment method: {method}'
        print(f"[PayMongo] Error: {error_msg}")
        return jsonify({'error': error_msg}), 400

    # Build success/failure redirect URLs
    success_url = f'{APP_BASE_URL}/api/paymongo/success?booking_id={booking_id}'
    cancel_url = f'{APP_BASE_URL}/api/paymongo/cancel?booking_id={booking_id}'

    # Create PayMongo Payment Link
    payload = {
        'data': {
            'attributes': {
                'amount': amount_centavos,
                'currency': 'PHP',
                'description': description,
                'payment_method_types': [pm_type],
                'success_url': success_url,
                'cancel_url': cancel_url,
                'metadata': {
                    'booking_id': str(booking_id),
                    'method': method,
                    'payment_type': payment_type
                }
            }
        }
    }

    # Add billing info if provided
    if customer_email or customer_name:
        billing = {}
        if customer_name:
            billing['name'] = customer_name
        if customer_email:
            billing['email'] = customer_email
        if customer_phone:
            billing['phone'] = customer_phone
        payload['data']['attributes']['billing'] = billing

    try:
        res = requests.post(
            f'{PAYMONGO_API}/links',
            headers=get_auth_header(),
            json=payload,
            timeout=15
        )
        result = res.json()

        if res.status_code not in (200, 201):
            error_msg = result.get('errors', [{}])[0].get('detail', 'PayMongo error')
            return jsonify({'error': error_msg}), res.status_code

        link_data = result['data']
        link_id = link_data['id']
        checkout_url = link_data['attributes']['checkout_url']
        reference_number = link_data['attributes']['reference_number']

        # Store the PayMongo link ID in the booking for webhook matching (only for non-extensions)
        if payment_type != 'Extension':
            cur = get_cursor()
            cur.execute(
                "UPDATE bookings SET paymongo_link_id = %s WHERE id = %s",
                (link_id, booking_id)
            )
            commit_db()

        return jsonify({
            'checkout_url': checkout_url,
            'link_id': link_id,
            'reference_number': reference_number,
            'amount': amount,
            'method': method
        }), 200

    except requests.exceptions.Timeout:
        return jsonify({'error': 'PayMongo request timed out. Please try again.'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ??? PAYMENT SUCCESS REDIRECT ????????????????????????????????????????????????

@paymongo_bp.route('/paymongo/success', methods=['GET'])
@paymongo_bp.route('/api/paymongo/success', methods=['GET'])
def payment_success():
    """
    PayMongo redirects here after successful payment.
    Verifies payment and updates booking status.
    """
    booking_id = request.args.get('booking_id')
    if not booking_id:
        return '<h2>Payment confirmed. Please return to the app.</h2>', 200

    try:
        cur = get_cursor()
        cur.execute("SELECT paymongo_link_id, payment_type, payment_status, total_price FROM bookings WHERE id = %s", (booking_id,))
        booking = cur.fetchone()

        if booking and booking['paymongo_link_id']:
            # Verify with PayMongo API
            res = requests.get(
                f"{PAYMONGO_API}/links/{booking['paymongo_link_id']}",
                headers=get_auth_header(),
                timeout=10
            )
            if res.status_code == 200:
                link = res.json()['data']
                status = link['attributes']['status']
                payments = link['attributes'].get('payments', [])

                if status == 'paid':
                    method = 'online'
                    ref_num = booking['paymongo_link_id']
                    amount_paid = float(booking.get('total_price') or 0)
                    if payments:
                        try:
                            p = payments[0]
                            p_attrs = p.get('data', p).get('attributes', p)
                            method = p_attrs.get('source', {}).get('type', 'online')
                            ref_num = p.get('data', p).get('id', ref_num)
                            raw_amount = p_attrs.get('amount', 0)
                            if raw_amount > 0:
                                amount_paid = raw_amount / 100
                        except Exception:
                            pass
                    
                    link_metadata = link['attributes'].get('metadata', {})
                    pay_type = link_metadata.get('payment_type') or booking['payment_type'] or 'Full'
                    
                    _confirm_payment(booking_id, amount_paid, method, ref_num, pay_type)

        # Redirect back to app with deep link
        return f'''
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                * {{ margin:0; padding:0; box-sizing:border-box; }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                       background: #0f172a; color: white;
                       display: flex; align-items: center; justify-content: center;
                       min-height: 100vh; flex-direction: column; gap: 16px;
                       padding: 32px 24px; text-align: center; }}
                .check {{ width:80px; height:80px; border-radius:50%;
                          background: rgba(52,211,153,0.15); border: 2px solid #34d399;
                          display:flex; align-items:center; justify-content:center;
                          font-size:2.5rem; margin-bottom:8px; }}
                h2 {{ font-size: 1.6rem; font-weight: 800; color: #34d399; margin-bottom:6px; }}
                p {{ color: #94a3b8; font-size: 0.9rem; line-height:1.5; }}
                .btn {{ background: #e63946; color: white; padding: 16px 32px;
                        border-radius: 14px; text-decoration: none; font-weight: 700;
                        font-size: 1rem; display: inline-block; margin-top: 24px;
                        border: none; cursor: pointer; width: 100%; max-width: 320px; }}
                .btn-outline {{ background: transparent; border: 2px solid #334155;
                                color: #94a3b8; margin-top: 10px; }}
                small {{ color: #475569; font-size: 0.75rem; margin-top: 8px; display:block; }}
            </style>
        </head>
        <body>
            <div class="check">&#10003;</div>
            <h2>Payment Successful!</h2>
            <p>Booking #{booking_id} has been confirmed.<br>Tap the button below to return to Autoride.</p>
            <a href="com.autoride.customer://payment-success?booking_id={booking_id}" class="btn"
               onclick="this.textContent='Returning...'">
                &#8592; Return to Autoride App
            </a>
            <small>If the button doesn\'t work, close this window and tap "I\'ve Completed Payment" in the app.</small>
        </body>
        <script>
            // Auto-redirect after 2 seconds
            setTimeout(function() {{
                window.location.href = 'com.autoride.customer://payment-success?booking_id={booking_id}';
            }}, 2000);
        </script>
        </html>
        ''', 200

    except Exception as e:
        return f'<h2>Payment received. Booking #{booking_id} is being processed.</h2>', 200


# ??? PAYMENT CANCEL REDIRECT ?????????????????????????????????????????????????

@paymongo_bp.route('/paymongo/cancel', methods=['GET'])
@paymongo_bp.route('/api/paymongo/cancel', methods=['GET'])
def payment_cancel():
    """PayMongo redirects here if user cancels payment."""
    booking_id = request.args.get('booking_id')
    return f'''
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #0a0a0a; color: white;
                   display: flex; align-items: center; justify-content: center; min-height: 100vh;
                   flex-direction: column; gap: 16px; padding: 20px; text-align: center; }}
            .icon {{ font-size: 4rem; }}
            h2 {{ font-size: 1.5rem; font-weight: 800; color: #f87171; }}
            p {{ color: #94a3b8; font-size: 0.9rem; }}
            a {{ background: #1e293b; color: white; padding: 14px 28px; border-radius: 12px;
                 text-decoration: none; font-weight: 700; display: inline-block; margin-top: 10px;
                 border: 1px solid rgba(255,255,255,0.1); }}
        </style>
    </head>
    <body>
        <div class="icon">?</div>
        <h2>Payment Cancelled</h2>
        <p>Your booking #{booking_id} is still pending.</p>
        <p>You can try again from the app.</p>
        <a href="javascript:window.close()">Return to App</a>
    </body>
    </html>
    ''', 200


# ??? WEBHOOK ?????????????????????????????????????????????????????????????????

@paymongo_bp.route('/paymongo/webhook', methods=['POST'])
@paymongo_bp.route('/api/paymongo/webhook', methods=['POST'])
def paymongo_webhook():
    """
    PayMongo sends payment events here.
    Verifies signature and processes payment.payment.paid events.
    """
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Paymongo-Signature', '')

    # Verify webhook signature
    if PAYMONGO_WEBHOOK_SECRET and sig_header:
        try:
            parts = dict(p.split('=', 1) for p in sig_header.split(','))
            timestamp = parts.get('t', '')
            test_sig = parts.get('te', parts.get('li', ''))
            signed_payload = f'{timestamp}.{payload}'
            expected = hmac.new(
                PAYMONGO_WEBHOOK_SECRET.encode(),
                signed_payload.encode(),
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(expected, test_sig):
                return jsonify({'error': 'Invalid signature'}), 400
        except Exception:
            pass  # Don't block if signature check fails in dev

    try:
        event = json.loads(payload)
        event_type = event.get('data', {}).get('attributes', {}).get('type', '')

        if event_type == 'payment.paid':
            payment_attrs = event['data']['attributes']['data']['attributes']
            metadata = payment_attrs.get('metadata', {})
            booking_id = metadata.get('booking_id')
            amount = payment_attrs.get('amount', 0) / 100
            method = payment_attrs.get('source', {}).get('type', 'online')
            ref_num = event['data']['attributes']['data']['id']

            if booking_id:
                payment_type = metadata.get('payment_type', 'Full')
                if payment_type == 'Extension':
                    # Extension payment is confirmed by the frontend calling check_payment_status,
                    # and the extension is submitted to the backend as pending.
                    pass
                else:
                    cur = get_cursor()
                    cur.execute("SELECT payment_type, payment_status FROM bookings WHERE id = %s", (booking_id,))
                    booking = cur.fetchone()
                    if booking:
                        _confirm_payment(booking_id, amount, method, ref_num, payment_type)

        return jsonify({'received': True}), 200

    except Exception as e:
        print(f'WEBHOOK ERROR: {e}')
        return jsonify({'error': str(e)}), 500


# ??? CHECK PAYMENT STATUS ?????????????????????????????????????????????????????

@paymongo_bp.route('/paymongo/status/<int:booking_id>', methods=['GET'])
@paymongo_bp.route('/api/paymongo/status/<int:booking_id>', methods=['GET'])
def check_payment_status(booking_id):
    """
    Poll payment status. Actively checks PayMongo API if not yet confirmed in DB.
    """
    try:
        query_link_id = request.args.get('link_id')
        
        cur = get_cursor()
        cur.execute(
            "SELECT status, payment_status, paymongo_link_id, payment_type, total_price FROM bookings WHERE id = %s",
            (booking_id,)
        )
        booking = cur.fetchone()
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404

        # Already confirmed in DB (Only applies if we aren't checking a specific new link)
        if not query_link_id and booking['payment_status'] == 'Paid':
            return jsonify({
                'booking_id': booking_id,
                'status': booking['status'],
                'payment_status': booking['payment_status'],
                'paid': True
            }), 200

        # Not yet confirmed - actively check PayMongo API
        link_id = query_link_id or booking['paymongo_link_id']
        debug_info = {'link_id': link_id, 'has_key': bool(PAYMONGO_SECRET_KEY)}
        if link_id and PAYMONGO_SECRET_KEY:
            try:
                res = requests.get(
                    f'{PAYMONGO_API}/links/{link_id}',
                    headers=get_auth_header(),
                    timeout=10
                )
                debug_info['paymongo_http'] = res.status_code
                if res.status_code == 200:
                    link_data = res.json()['data']
                    link_status = link_data['attributes']['status']
                    payments = link_data['attributes'].get('payments', [])
                    debug_info['link_status'] = link_status
                    debug_info['payments_count'] = len(payments)

                    # PayMongo paid link - process payment
                    if link_status == 'paid':
                        # If this is an extension payment, we just return paid status without triggering full payment confirmation
                        is_extension = bool(query_link_id and query_link_id != booking['paymongo_link_id'])
                        if is_extension:
                            return jsonify({'booking_id': booking_id, 'paid': True, 'is_extension': True}), 200
                            
                        # Try to get payment details from payments array
                        method = 'online'
                        ref_num = link_id
                        amount_paid = float(booking.get('total_price') or 0)

                        if payments:
                            try:
                                p = payments[0]
                                # Handle both nested and flat payment structures
                                p_attrs = p.get('data', p).get('attributes', p)
                                method = p_attrs.get('source', {}).get('type', 'online')
                                ref_num = p.get('data', p).get('id', link_id)
                                raw_amount = p_attrs.get('amount', 0)
                                if raw_amount > 0:
                                    amount_paid = raw_amount / 100
                            except Exception as parse_err:
                                debug_info['parse_error'] = str(parse_err)

                        link_metadata = link_data['attributes'].get('metadata', {})
                        pay_type = link_metadata.get('payment_type') or booking['payment_type'] or 'Full'
                        
                        _confirm_payment(booking_id, amount_paid, method, ref_num, pay_type)
                        new_status = 'Partially Paid' if pay_type == 'Downpayment' else 'Paid'
                        return jsonify({
                            'booking_id': booking_id,
                            'status': 'Confirmed',
                            'payment_status': new_status,
                            'paid': True
                        }), 200
                else:
                    debug_info['paymongo_error'] = res.json()
            except Exception as pm_err:
                debug_info['exception'] = str(pm_err)
                print(f'PayMongo API check error: {pm_err}')

        return jsonify({
            'booking_id': booking_id,
            'status': booking['status'],
            'payment_status': booking['payment_status'],
            'paid': False,
            'debug': debug_info
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def check_and_update_unpaid_paymongo_bookings(user_id=None):
    """
    Finds bookings that are 'Unpaid' or 'Downpayment unpaid' but have a paymongo_link_id,
    polls the PayMongo API for their status, and updates them if they are paid.
    """
    try:
        # Auto-cancel pending bookings that have not paid deposit within 30 minutes
        try:
            cancel_cur = get_cursor()
            cancel_cur.execute("""
                UPDATE bookings
                SET status = 'Cancelled',
                    payment_status = 'Expired',
                    cancellation_reason = 'Reservation deposit expired (not paid within 30 minutes)'
                WHERE (status IN ('Pending', 'pending', 'Pending Payment') OR payment_status IN ('Unpaid', 'Pending Payment', 'Downpayment unpaid'))
                  AND payment_status NOT IN ('Paid', 'Partially Paid', 'Refunded', 'Cancelled')
                  AND created_at < NOW() - INTERVAL '30 minutes'
                RETURNING id, vehicle_id, user_id
            """)
            expired_rows = cancel_cur.fetchall() or []
            for erow in expired_rows:
                if erow.get('vehicle_id'):
                    cancel_cur.execute("UPDATE vehicles SET status = 'Available' WHERE id = %s", (erow['vehicle_id'],))
            commit_db()
            cancel_cur.close()
        except Exception as _ce:
            print(f"[PayMongo] Auto-cancel expired pending bookings error: {_ce}")
            try:
                get_db().rollback()
            except Exception:
                pass

        cur = get_cursor()
        if user_id:
            cur.execute(
                "SELECT id, paymongo_link_id, payment_status, payment_type, total_price FROM bookings "
                "WHERE user_id = %s AND payment_status IN ('Unpaid', 'Downpayment unpaid') AND paymongo_link_id IS NOT NULL AND paymongo_link_id != ''",
                (user_id,)
            )
        else:
            cur.execute(
                "SELECT id, paymongo_link_id, payment_status, payment_type, total_price FROM bookings "
                "WHERE payment_status IN ('Unpaid', 'Downpayment unpaid') AND paymongo_link_id IS NOT NULL AND paymongo_link_id != ''"
            )
        unpaid_bookings = cur.fetchall()
        cur.close()
        
        # Release the connection back to the pool before doing slow HTTP requests
        from flask import g
        conn = g.pop('db_conn', None)
        if conn:
            try:
                conn.commit()
                conn.close()
            except Exception:
                pass
        
        for booking in unpaid_bookings:
            booking_id = booking['id']
            link_id = booking['paymongo_link_id']
            if not PAYMONGO_SECRET_KEY or not link_id:
                continue
                
            try:
                res = requests.get(
                    f'{PAYMONGO_API}/links/{link_id}',
                    headers=get_auth_header(),
                    timeout=5
                )
                if res.status_code == 200:
                    link_data = res.json()['data']
                    link_status = link_data['attributes']['status']
                    if link_status == 'paid':
                        payments = link_data['attributes'].get('payments', [])
                        method = 'online'
                        ref_num = link_id
                        amount_paid = float(booking.get('total_price') or 0)
                        if payments:
                            try:
                                p = payments[0]
                                p_attrs = p.get('data', p).get('attributes', p)
                                method = p_attrs.get('source', {}).get('type', 'online')
                                ref_num = p.get('data', p).get('id', link_id)
                                raw_amount = p_attrs.get('amount', 0)
                                if raw_amount > 0:
                                    amount_paid = raw_amount / 100
                            except Exception:
                                pass
                        
                        link_metadata = link_data['attributes'].get('metadata', {})
                        pay_type = link_metadata.get('payment_type') or booking['payment_type'] or 'Full'
                        
                        _confirm_payment(booking_id, amount_paid, method, ref_num, pay_type)
            except Exception as pm_err:
                print(f"Automatic PayMongo status check error for booking {booking_id}: {pm_err}")
    except Exception as e:
        print(f"Error checking unpaid bookings: {e}")


# ??? INTERNAL HELPER ?????????????????????????????????????????????????????????


def _confirm_payment(booking_id, amount, method, ref_num, payment_type):
    """Internal: record payment and update booking status."""
    try:
        cur = get_cursor()

        # Check if already paid (idempotency)
        cur.execute("SELECT payment_status FROM bookings WHERE id = %s", (booking_id,))
        b = cur.fetchone()
        if b:
            if b['payment_status'] == 'Paid':
                return  # Already processed
            if payment_type == 'Downpayment' and b['payment_status'] == 'Partially Paid':
                return  # Downpayment already processed

        # Insert payment record
        cur.execute("""
            INSERT INTO payments (booking_id, amount, method, reference_number, status)
            VALUES (%s, %s, %s, %s, 'Completed')
            RETURNING id
        """, (booking_id, amount, method, ref_num))
        payment_id = cur.fetchone()['id']

        # Get booking total price
        cur.execute("SELECT total_price, amount_paid FROM bookings WHERE id = %s", (booking_id,))
        bk_data = cur.fetchone()
        total_price = float(bk_data['total_price'] or 0) if bk_data else 0.0

        # Determine payment status, amount_paid, and balance_amount
        if payment_type == 'Downpayment':
            new_payment_status = 'Partially Paid'
            new_amount_paid = float(amount)
            new_balance_amount = total_price - new_amount_paid
        elif payment_type == 'Balance':
            new_payment_status = 'Paid'
            new_amount_paid = total_price
            new_balance_amount = 0.0
        else: # Full
            new_payment_status = 'Paid'
            new_amount_paid = float(amount) if float(amount) > 0 else total_price
            new_balance_amount = 0.0

        # Update booking
        cur.execute("""
            UPDATE bookings
            SET status = 'Confirmed', 
                payment_status = %s,
                amount_paid = %s,
                balance_amount = %s
            WHERE id = %s
        """, (new_payment_status, new_amount_paid, new_balance_amount, booking_id))

        # Update vehicle status
        cur.execute("""
            UPDATE vehicles SET status = 'Booked'
            WHERE id = (SELECT vehicle_id FROM bookings WHERE id = %s)
        """, (booking_id,))

        # Update loyalty points
        cur.execute(
            "SELECT user_id, points_earned, points_redeemed, applied_coupon_id FROM bookings WHERE id = %s",
            (booking_id,)
        )
        bk = cur.fetchone()
        if bk:
            earned = bk['points_earned'] or 0
            redeemed = bk['points_redeemed'] or 0
            cur.execute(
                "UPDATE users SET loyalty_points = loyalty_points + %s - %s WHERE id = %s",
                (earned, redeemed, bk['user_id'])
            )
            if bk['applied_coupon_id']:
                cur.execute(
                    "UPDATE coupons SET times_used = times_used + 1 WHERE id = %s",
                    (bk['applied_coupon_id'],)
                )

        commit_db()

        # Send notifications (in-app)
        try:
            from notifications import notification_service
            cur.execute(
                "SELECT user_id, total_price, amount_paid, balance_amount FROM bookings WHERE id = %s",
                (booking_id,)
            )
            bk2 = cur.fetchone()
            if bk2:
                uid = bk2['user_id']
                amt = float(bk2['amount_paid'] or amount)
                bal = float(bk2['balance_amount'] or 0)
                if payment_type == 'Downpayment':
                    notification_service.notify_user(
                        uid,
                        'Downpayment Received',
                        f'Downpayment of PHP {amt:.2f} received for booking #{booking_id} via {method}. Remaining balance: PHP {bal:.2f}.',
                        'payment_downpayment'
                    )
                else:
                    notification_service.notify_user(
                        uid,
                        'Payment Confirmed',
                        f'Payment of PHP {amt:.2f} confirmed for booking #{booking_id} via {method}. Ref: {ref_num}.',
                        'payment_confirmed'
                    )
                
                # Notify admins about the new payment
                try:
                    cur.execute("SELECT full_name FROM users WHERE id = %s", (uid,))
                    u_row = cur.fetchone()
                    uname = u_row['full_name'] if u_row else f'User #{uid}'
                    notification_service.notify_admins_inapp(
                        "New Payment Received",
                        f"Booking #{booking_id} - PHP {amt:.2f} paid via {method} by {uname}.",
                        'admin_payment_proof',
                        type='admin_payment_proof',
                        booking_id=booking_id
                    )
                except Exception as admin_notif_err:
                    print(f"Admin notification error: {admin_notif_err}")
        except Exception as notif_err:
            print(f'_confirm_payment notification error: {notif_err}')
            # Rollback any aborted transaction state so email query can still run
            try:
                get_db().rollback()
            except Exception:
                pass

        # Send receipt email
        try:
            cur.execute("""
                SELECT b.id, u.full_name, u.email, v.brand, v.model,
                       b.start_date, b.end_date, b.total_price, b.amount_paid,
                       b.addons, b.insurance_type, b.insurance_price,
                       b.base_price, b.addon_price, b.discount_amount,
                       b.payment_type, b.balance_amount,
                       p.reference_number, p.method
                FROM bookings b
                JOIN users u ON b.user_id = u.id
                JOIN vehicles v ON b.vehicle_id = v.id
                JOIN payments p ON p.booking_id = b.id
                WHERE b.id = %s AND p.id = %s
            """, (booking_id, payment_id))
            receipt = cur.fetchone()
            if receipt:
                from app import send_receipt_email
                send_receipt_email(receipt['email'], dict(receipt))
        except Exception as email_err:
            print(f'Receipt email error: {email_err}')

    except Exception as e:
        print(f'_confirm_payment error: {e}')
