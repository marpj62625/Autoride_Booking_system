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
from flask import Blueprint, request, jsonify, redirect
from database import get_cursor, commit_db, get_db
from config import PAYMONGO_SECRET_KEY, PAYMONGO_PUBLIC_KEY, PAYMONGO_WEBHOOK_SECRET, APP_BASE_URL

paymongo_bp = Blueprint('paymongo', __name__)

PAYMONGO_API = 'https://api.paymongo.com/v1'

def get_paymongo_config():
    """
    Fetch PayMongo configuration dynamically from the database `settings` table.
    Falls back to config.py / environment variables if not set in DB.
    """
    mode = 'test'
    test_sk = ''
    test_pk = ''
    live_sk = ''
    live_pk = ''
    wh_sec = ''

    try:
        cur = get_cursor()
        cur.execute("""
            SELECT key, value FROM settings 
            WHERE key IN (
                'paymongo_mode', 
                'paymongo_test_secret_key', 
                'paymongo_test_public_key', 
                'paymongo_live_secret_key', 
                'paymongo_live_public_key', 
                'paymongo_webhook_secret'
            )
        """)
        rows = cur.fetchall() or []
        for r in rows:
            k = r.get('key')
            v = (r.get('value') or '').strip()
            if k == 'paymongo_mode':
                mode = v.lower() if v.lower() in ('test', 'live') else 'test'
            elif k == 'paymongo_test_secret_key':
                test_sk = v
            elif k == 'paymongo_test_public_key':
                test_pk = v
            elif k == 'paymongo_live_secret_key':
                live_sk = v
            elif k == 'paymongo_live_public_key':
                live_pk = v
            elif k == 'paymongo_webhook_secret':
                wh_sec = v
        cur.close()
    except Exception as e:
        print(f"[PayMongo Config] DB read error, using env fallback: {e}")

    # Resolve active credentials based on selected mode
    if mode == 'live':
        active_sk = live_sk
        active_pk = live_pk
        # Only fall back to env var if it's explicitly a LIVE key
        if not active_sk and PAYMONGO_SECRET_KEY and PAYMONGO_SECRET_KEY.startswith('sk_live_'):
            active_sk = PAYMONGO_SECRET_KEY
        if not active_pk and PAYMONGO_PUBLIC_KEY and PAYMONGO_PUBLIC_KEY.startswith('pk_live_'):
            active_pk = PAYMONGO_PUBLIC_KEY
    else:
        active_sk = test_sk or PAYMONGO_SECRET_KEY
        active_pk = test_pk or PAYMONGO_PUBLIC_KEY

    active_wh = wh_sec or PAYMONGO_WEBHOOK_SECRET

    return {
        'mode': mode,
        'secret_key': active_sk,
        'public_key': active_pk,
        'webhook_secret': active_wh,
        'test_secret_key': test_sk,
        'test_public_key': test_pk,
        'live_secret_key': live_sk,
        'live_public_key': live_pk
    }

def get_auth_header():
    """Base64 encode the active secret key for PayMongo Basic Auth."""
    cfg = get_paymongo_config()
    secret_key = cfg.get('secret_key', '')
    encoded = base64.b64encode(f'{secret_key}:'.encode()).decode()
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
    client = data.get('client', 'mobile')  # 'web' or 'mobile'

    # Log incoming request for debugging
    print(f"[PayMongo] Create payment request: booking_id={booking_id}, amount={amount}, method={method}, client={client}")

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

    cfg = get_paymongo_config()
    active_sk = cfg.get('secret_key', '')
    active_mode = cfg.get('mode', 'test')

    if not active_sk:
        error_msg = f'PayMongo is configured for {active_mode.upper()} mode, but no Secret Key is set. Please enter and save your key in Admin Settings.'
        print(f"[PayMongo] Error: {error_msg}")
        return jsonify({'error': error_msg}), 400

    if active_mode == 'live' and active_sk.startswith('sk_test_'):
        error_msg = 'PayMongo mode is set to LIVE, but the active Secret Key is a TEST key (sk_test_). Please enter your Live Secret Key (starts with sk_live_) in Admin Settings.'
        print(f"[PayMongo] Error: {error_msg}")
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

    # Build success/failure redirect URLs based on client platform
    if client == 'web':
        success_url = f'{APP_BASE_URL}/api/paymongo/success?booking_id={booking_id}&client=web'
        cancel_url = f'{APP_BASE_URL}/api/paymongo/cancel?booking_id={booking_id}&client=web'
    else:
        success_url = f'{APP_BASE_URL}/api/paymongo/success?booking_id={booking_id}'
        cancel_url = f'{APP_BASE_URL}/api/paymongo/cancel?booking_id={booking_id}'

    # Billing details if provided
    billing = {}
    if customer_name and customer_name.strip():
        billing['name'] = customer_name.strip()
    if customer_email and '@' in customer_email and '.' in customer_email:
        billing['email'] = customer_email.strip()
    if customer_phone and customer_phone.strip():
        billing['phone'] = customer_phone.strip()

    # Map method names for Checkout Sessions (supports native auto-redirect)
    cs_method_map = {
        'gcash': ['gcash', 'qrph'],
        'maya': ['paymaya', 'qrph'],
        'paymaya': ['paymaya', 'qrph'],
        'card': ['card'],
        'credit_card': ['card'],
        'debit_card': ['card'],
    }
    cs_pm_types = cs_method_map.get(method.lower(), [pm_type, 'qrph'])

    cs_payload = {
        'data': {
            'attributes': {
                'send_email_receipt': False,
                'show_description': True,
                'show_line_items': True,
                'line_items': [
                    {
                        'name': description,
                        'amount': amount_centavos,
                        'currency': 'PHP',
                        'quantity': 1
                    }
                ],
                'payment_method_types': cs_pm_types,
                'success_url': success_url,
                'cancel_url': cancel_url,
                'description': description,
                'metadata': {
                    'booking_id': str(booking_id),
                    'method': method,
                    'payment_type': payment_type,
                    'client': client
                }
            }
        }
    }
    if billing:
        cs_payload['data']['attributes']['billing'] = billing

    # Legacy Payment Link payload as fallback
    link_payload = {
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
                    'payment_type': payment_type,
                    'client': client
                }
            }
        }
    }
    if billing:
        link_payload['data']['attributes']['billing'] = billing

    try:
        # Try Checkout Sessions first (PayMongo's modern hosted checkout with automatic success redirect)
        res = requests.post(
            f'{PAYMONGO_API}/checkout_sessions',
            headers=get_auth_header(),
            json=cs_payload,
            timeout=15
        )
        result = res.json()

        # If checkout session creation fails, fallback to legacy links
        if res.status_code not in (200, 201):
            print(f"[PayMongo] Checkout session failed ({res.status_code}), falling back to links: {res.text}")
            res = requests.post(
                f'{PAYMONGO_API}/links',
                headers=get_auth_header(),
                json=link_payload,
                timeout=15
            )
            result = res.json()

        if res.status_code not in (200, 201):
            error_msg = result.get('errors', [{}])[0].get('detail', 'PayMongo error')
            return jsonify({'error': error_msg}), res.status_code

        res_data = result['data']
        link_id = res_data['id']
        checkout_url = res_data['attributes']['checkout_url']
        reference_number = res_data['attributes'].get('reference_number') or link_id

        # Store the PayMongo session/link ID in the booking for webhook matching (only for non-extensions)
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
    client = request.args.get('client', 'mobile')
    if not booking_id:
        if client == 'web':
            return redirect(f'{APP_BASE_URL}/')
        return '<h2>Payment confirmed. Please return to the app.</h2>', 200

    try:
        cur = get_cursor()
        cur.execute("SELECT paymongo_link_id, payment_type, payment_status, total_price FROM bookings WHERE id = %s", (booking_id,))
        booking = cur.fetchone()

        if booking and booking['paymongo_link_id']:
            link_id = booking['paymongo_link_id']
            endpoint = f"{PAYMONGO_API}/checkout_sessions/{link_id}" if link_id.startswith('cs_') else f"{PAYMONGO_API}/links/{link_id}"
            res = requests.get(
                endpoint,
                headers=get_auth_header(),
                timeout=10
            )
            if res.status_code == 200:
                link = res.json()['data']
                link_attrs = link['attributes']
                status = link_attrs.get('status')
                payment_intent = link_attrs.get('payment_intent', {})
                pi_status = payment_intent.get('attributes', {}).get('status') or payment_intent.get('status')
                payments = link_attrs.get('payments', [])

                is_paid = (status == 'paid') or (pi_status == 'succeeded')
                if not is_paid and payments:
                    for p in payments:
                        p_attrs = p.get('data', p).get('attributes', p)
                        if p_attrs.get('status') == 'paid':
                            is_paid = True
                            break

                if is_paid:
                    method = 'online'
                    ref_num = link_id
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

        # If web client, redirect directly to web application with payment=success
        if client == 'web':
            return redirect(f'{APP_BASE_URL}/?payment=success&booking_id={booking_id}')

        # Redirect back to mobile app with deep link
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
    client = request.args.get('client', 'mobile')
    if client == 'web':
        return redirect(f'{APP_BASE_URL}/?payment=cancelled&booking_id={booking_id or ""}')
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

    # Verify webhook signature using active dynamic secret
    cfg = get_paymongo_config()
    wh_secret = cfg.get('webhook_secret') or PAYMONGO_WEBHOOK_SECRET

    if wh_secret and sig_header:
        try:
            parts = dict(p.split('=', 1) for p in sig_header.split(','))
            timestamp = parts.get('t', '')
            test_sig = parts.get('te', parts.get('li', ''))
            signed_payload = f'{timestamp}.{payload}'
            expected = hmac.new(
                wh_secret.encode(),
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

        if event_type in ('payment.paid', 'checkout_session.payment.paid'):
            event_data = event.get('data', {}).get('attributes', {}).get('data', {})
            payment_attrs = event_data.get('attributes', {})
            metadata = payment_attrs.get('metadata', {})
            booking_id = metadata.get('booking_id')
            raw_amount = payment_attrs.get('amount', 0)
            payments = payment_attrs.get('payments', [])
            method = 'online'
            if payments:
                try:
                    p = payments[0]
                    p_attrs = p.get('data', p).get('attributes', p)
                    method = p_attrs.get('source', {}).get('type', 'online')
                    if raw_amount == 0 and p_attrs.get('amount'):
                        raw_amount = p_attrs.get('amount')
                except Exception:
                    pass
            elif payment_attrs.get('source'):
                method = payment_attrs.get('source', {}).get('type', 'online')

            amount = raw_amount / 100 if raw_amount else 0
            ref_num = event_data.get('id', 'online')

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
        cfg = get_paymongo_config()
        secret_key = cfg.get('secret_key')
        debug_info = {'link_id': link_id, 'has_key': bool(secret_key)}
        if link_id and secret_key:
            try:
                endpoint = f'{PAYMONGO_API}/checkout_sessions/{link_id}' if link_id.startswith('cs_') else f'{PAYMONGO_API}/links/{link_id}'
                res = requests.get(
                    endpoint,
                    headers=get_auth_header(),
                    timeout=10
                )
                debug_info['paymongo_http'] = res.status_code
                if res.status_code == 200:
                    link_data = res.json()['data']
                    link_attrs = link_data['attributes']
                    link_status = link_attrs.get('status')
                    payment_intent = link_attrs.get('payment_intent', {})
                    pi_status = payment_intent.get('attributes', {}).get('status') or payment_intent.get('status')
                    payments = link_attrs.get('payments', [])
                    debug_info['link_status'] = link_status
                    debug_info['payments_count'] = len(payments)

                    # Determine if paid
                    is_paid = (link_status == 'paid') or (pi_status == 'succeeded')
                    if not is_paid and payments:
                        for p in payments:
                            p_attrs = p.get('data', p).get('attributes', p)
                            if p_attrs.get('status') == 'paid':
                                is_paid = True
                                break

                    # PayMongo paid link or session - process payment
                    if is_paid:
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
                        pay_type = link_metadata.get('payment_type') or booking.get('payment_type') or 'Full'
                        
                        _confirm_payment(booking_id, amount_paid, method, ref_num, pay_type)

                        # Fetch fresh booking status directly from DB
                        cur.execute("SELECT status, payment_status, amount_paid, balance_amount FROM bookings WHERE id = %s", (booking_id,))
                        updated_b = cur.fetchone()
                        new_status = updated_b['payment_status'] if updated_b else ('Paid' if pay_type != 'Downpayment' else 'Partially Paid')
                        new_bk_status = updated_b['status'] if updated_b else 'Confirmed'
                        return jsonify({
                            'booking_id': booking_id,
                            'status': new_bk_status,
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
            # Apply violation strikes for each expired booking
            if expired_rows:
                try:
                    _apply_violation_strikes(expired_rows)
                except Exception as _ve:
                    print(f"[Violation] Strike apply error: {_ve}")
        except Exception as _ce:
            print(f"[PayMongo] Auto-cancel expired pending bookings error: {_ce}")
            try:
                get_db().rollback()
            except Exception:
                pass

        # Send payment deadline warnings (15-min and 5-min)
        try:
            _send_payment_deadline_warnings()
        except Exception as _pw:
            print(f"[Violation] Payment warning error: {_pw}")

        cur = get_cursor()
        if user_id:
            cur.execute(
                "SELECT id, paymongo_link_id, payment_status, payment_type, total_price FROM bookings "
                "WHERE user_id = %s AND payment_status IN ('Unpaid', 'Downpayment unpaid', 'Partially Paid') AND paymongo_link_id IS NOT NULL AND paymongo_link_id != ''",
                (user_id,)
            )
        else:
            cur.execute(
                "SELECT id, paymongo_link_id, payment_status, payment_type, total_price FROM bookings "
                "WHERE payment_status IN ('Unpaid', 'Downpayment unpaid', 'Partially Paid') AND paymongo_link_id IS NOT NULL AND paymongo_link_id != ''"
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
        
        cfg = get_paymongo_config()
        secret_key = cfg.get('secret_key')
        for booking in unpaid_bookings:
            booking_id = booking['id']
            link_id = booking['paymongo_link_id']
            if not secret_key or not link_id:
                continue
                
            try:
                endpoint = f'{PAYMONGO_API}/checkout_sessions/{link_id}' if link_id.startswith('cs_') else f'{PAYMONGO_API}/links/{link_id}'
                res = requests.get(
                    endpoint,
                    headers=get_auth_header(),
                    timeout=5
                )
                if res.status_code == 200:
                    link_data = res.json()['data']
                    link_attrs = link_data['attributes']
                    link_status = link_attrs.get('status')
                    payment_intent = link_attrs.get('payment_intent', {})
                    pi_status = payment_intent.get('attributes', {}).get('status') or payment_intent.get('status')
                    payments = link_attrs.get('payments', [])

                    is_paid = (link_status == 'paid') or (pi_status == 'succeeded')
                    if not is_paid and payments:
                        for p in payments:
                            p_attrs = p.get('data', p).get('attributes', p)
                            if p_attrs.get('status') == 'paid':
                                is_paid = True
                                break

                    if is_paid:
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

        # Check if this exact payment transaction was already processed (true idempotency)
        if ref_num:
            cur.execute(
                "SELECT id FROM payments WHERE booking_id = %s AND reference_number = %s",
                (booking_id, str(ref_num))
            )
            if cur.fetchone():
                return  # Duplicate call for this specific payment transaction

        # Fetch current booking details
        cur.execute("""
            SELECT id, total_price, amount_paid, balance_amount, payment_status, payment_type, user_id, vehicle_id
            FROM bookings WHERE id = %s
        """, (booking_id,))
        bk_data = cur.fetchone()
        if not bk_data:
            return

        total_price = float(bk_data['total_price'] or 0)
        curr_amount_paid = float(bk_data['amount_paid'] or 0)
        curr_balance = float(bk_data['balance_amount'] or 0)
        curr_status = bk_data['payment_status']
        paid_amt = float(amount or 0)

        # If already fully paid, don't re-process as full payment
        if curr_status == 'Paid' and curr_balance <= 0.0:
            return

        # Insert payment record
        cur.execute("""
            INSERT INTO payments (booking_id, amount, method, reference_number, status)
            VALUES (%s, %s, %s, %s, 'Completed')
            RETURNING id
        """, (booking_id, paid_amt, method, str(ref_num)))
        payment_id = cur.fetchone()['id']

        # Determine payment status, amount_paid, and balance_amount
        # If the booking was already Partially Paid, or payment_type is Balance, or paid_amt covers the remaining balance:
        is_balance_or_full = (
            curr_status == 'Partially Paid' or
            payment_type in ('Balance', 'Full') or
            (curr_balance > 0 and paid_amt >= curr_balance - 1.0) or
            (curr_amount_paid + paid_amt >= total_price - 1.0)
        )

        if is_balance_or_full:
            new_payment_status = 'Paid'
            new_amount_paid = total_price
            new_balance_amount = 0.0
            new_payment_type = 'Full'
        elif payment_type == 'Downpayment':
            new_payment_status = 'Partially Paid'
            new_amount_paid = paid_amt
            new_balance_amount = max(0.0, total_price - new_amount_paid)
            new_payment_type = 'Downpayment'
        else: # Full
            new_payment_status = 'Paid'
            new_amount_paid = total_price
            new_balance_amount = 0.0
            new_payment_type = 'Full'

        # Update booking
        cur.execute("""
            UPDATE bookings
            SET status = CASE WHEN status = 'Pending' THEN 'Confirmed' ELSE status END, 
                payment_status = %s,
                amount_paid = %s,
                balance_amount = %s,
                payment_type = %s
            WHERE id = %s
        """, (new_payment_status, new_amount_paid, new_balance_amount, new_payment_type, booking_id))

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
                if new_payment_status == 'Partially Paid':
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
                        f'Payment of PHP {amt:.2f} confirmed for booking #{booking_id} via {method}. Ref: {ref_num}. Your booking is now fully paid!',
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


# ??? ADMIN PAYMONGO CREDENTIAL TEST ??????????????????????????????????????????

@paymongo_bp.route('/admin/paymongo/test-connection', methods=['POST'])
@paymongo_bp.route('/api/admin/paymongo/test-connection', methods=['POST'])
def test_paymongo_connection():
    """
    Super Admin endpoint to verify PayMongo credentials.
    Can test with provided secret_key in body or with stored database credentials.
    """
    data = request.get_json(silent=True) or {}
    mode = (data.get('mode') or '').lower()
    secret_key = (data.get('secret_key') or '').strip()

    # If secret_key not provided in body, load from active or mode-specific config
    if not secret_key:
        try:
            cfg = get_paymongo_config()
            if mode == 'live':
                secret_key = cfg.get('live_secret_key') or (cfg.get('secret_key') if cfg.get('mode') == 'live' else '')
            elif mode == 'test':
                secret_key = cfg.get('test_secret_key') or (cfg.get('secret_key') if cfg.get('mode') == 'test' else '')
            else:
                secret_key = cfg.get('secret_key')
        except Exception as cfg_err:
            print(f"Error fetching paymongo config: {cfg_err}")

    if not secret_key:
        return jsonify({'success': False, 'message': 'No Secret Key configured or entered to test.'}), 400

    # Helpful hint if user accidentally pasted public key
    if secret_key.startswith('pk_'):
        return jsonify({
            'success': False,
            'message': 'You entered a Public Key (starts with pk_). Please enter the Secret Key (starts with sk_test_ or sk_live_).'
        }), 400

    encoded = base64.b64encode(f'{secret_key}:'.encode()).decode()
    try:
        # PayMongo GET /v1/payments?limit=1 verifies secret key authentication
        res = requests.get(
            f'{PAYMONGO_API}/payments?limit=1',
            headers={'Authorization': f'Basic {encoded}', 'Content-Type': 'application/json'},
            timeout=10
        )
        if res.status_code == 200:
            key_type = 'Live' if secret_key.startswith('sk_live_') else 'Test'
            if mode == 'live' and key_type == 'Test':
                return jsonify({
                    'success': True,
                    'message': 'Warning: Valid PayMongo key, but it is a TEST key (sk_test_). For real customer payments, enter your LIVE Secret Key (sk_live_).',
                    'key_type': 'Test'
                }), 200
            return jsonify({
                'success': True,
                'message': f'Connection successful! Valid PayMongo {key_type} Secret Key.',
                'key_type': key_type
            }), 200
        elif res.status_code == 401:
            return jsonify({
                'success': False,
                'message': 'Invalid PayMongo Secret Key or unauthorized. Please verify the key in your PayMongo Dashboard.'
            }), 400
        else:
            try:
                err_data = res.json()
                err_msg = err_data.get('errors', [{}])[0].get('detail', f'PayMongo returned status {res.status_code}')
            except Exception:
                err_msg = f'PayMongo returned status {res.status_code}'
            return jsonify({'success': False, 'message': f'PayMongo rejected key: {err_msg}'}), 400
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'message': 'PayMongo request timed out. Check network connection.'}), 504
    except Exception as e:
        return jsonify({'success': False, 'message': f'Connection error: {str(e)}'}), 500


# ─── VIOLATION / STRIKE SYSTEM ───────────────────────────────────────────────


def _get_violation_settings():
    """Fetch violation system settings from DB. Returns a dict with defaults."""
    defaults = {
        'violation_max_strikes': 3,
        'violation_1st_suspension_hours': 24,
        'violation_2nd_suspension_days': 7,
        'violation_commitment_fee_amount': 200,
        'violation_auto_reset_clean_days': 30,
        'violation_warning_15min_enabled': 'true',
        'violation_warning_5min_enabled': 'true',
    }
    try:
        cur = get_cursor()
        cur.execute("SELECT key, value FROM settings WHERE key LIKE 'violation_%'")
        rows = cur.fetchall() or []
        cur.close()
        for row in rows:
            k, v = row['key'], row['value']
            if k in ('violation_max_strikes', 'violation_1st_suspension_hours',
                     'violation_2nd_suspension_days', 'violation_commitment_fee_amount',
                     'violation_auto_reset_clean_days'):
                try:
                    defaults[k] = int(v)
                except Exception:
                    pass
            else:
                defaults[k] = v
    except Exception as e:
        print(f"[Violation] Settings fetch error: {e}")
    return defaults


def _apply_violation_strikes(expired_rows):
    """
    Called after a booking is auto-cancelled for non-payment.
    Increments the user's violation strike count and applies
    the appropriate suspension based on strike number.
    """
    import psycopg
    from config import SUPABASE_DB_URL
    from psycopg.rows import dict_row
    from datetime import datetime, timedelta, timezone

    cfg = _get_violation_settings()
    max_strikes = cfg['violation_max_strikes']
    hours_1st = cfg['violation_1st_suspension_hours']
    days_2nd = cfg['violation_2nd_suspension_days']
    reset_days = cfg['violation_auto_reset_clean_days']

    for erow in expired_rows:
        uid = erow.get('user_id')
        booking_id = erow.get('id')
        if not uid:
            continue
        conn = None
        try:
            conn = psycopg.connect(conninfo=SUPABASE_DB_URL, autocommit=True, prepare_threshold=None)
            cur = conn.cursor(row_factory=dict_row)

            # Fetch current user violation state
            cur.execute("""
                SELECT violation_strikes, violation_last_at, violation_permanently_restricted
                FROM users WHERE id = %s
            """, (uid,))
            urow = cur.fetchone()
            if not urow:
                cur.close()
                continue

            # Skip if already permanently restricted
            if urow.get('violation_permanently_restricted'):
                cur.close()
                continue

            # Auto-reset strikes if enough clean days have passed
            current_strikes = int(urow.get('violation_strikes') or 0)
            last_at = urow.get('violation_last_at')
            now_utc = datetime.now(timezone.utc)
            if last_at and current_strikes > 0:
                if last_at.tzinfo is None:
                    last_at = last_at.replace(tzinfo=timezone.utc)
                days_since = (now_utc - last_at).days
                if days_since >= reset_days:
                    current_strikes = 0  # Auto-reset

            new_strikes = current_strikes + 1

            # Determine suspension
            suspension_until = None
            suspension_type = 'none'
            permanently_restricted = False

            if new_strikes == 1:
                suspension_until = now_utc + timedelta(hours=hours_1st)
                suspension_type = f'24h'
            elif new_strikes == 2:
                suspension_until = now_utc + timedelta(days=days_2nd)
                suspension_type = f'7d'
            elif new_strikes >= max_strikes:
                permanently_restricted = True
                suspension_type = 'permanent'

            # Update user record
            cur.execute("""
                UPDATE users
                SET violation_strikes = %s,
                    violation_last_at = NOW(),
                    booking_suspension_until = %s,
                    violation_commitment_fee_required = TRUE,
                    violation_permanently_restricted = %s
                WHERE id = %s
            """, (new_strikes, suspension_until, permanently_restricted, uid))

            # Insert violation history record
            cur.execute("""
                INSERT INTO user_violation_history
                    (user_id, booking_id, violation_number, suspension_type, suspension_until)
                VALUES (%s, %s, %s, %s, %s)
            """, (uid, booking_id, new_strikes, suspension_type, suspension_until))

            cur.close()

            # Send notification to user
            try:
                from notifications import Notification_Service
                ns = Notification_Service()
                if permanently_restricted:
                    msg = (
                        f'Strike #{new_strikes}: You have been permanently restricted from booking '
                        f'due to repeated failure to pay the reservation deposit. '
                        f'Please contact support.'
                    )
                elif new_strikes == 2:
                    msg = (
                        f'Strike #{new_strikes}: Your account has been suspended from booking for 7 days '
                        f'(until {suspension_until.strftime("%B %d, %Y")}) due to not completing '
                        f'your reservation deposit payment.'
                    )
                else:
                    msg = (
                        f'Strike #{new_strikes}: Your account has been suspended from booking for 24 hours '
                        f'(until {suspension_until.strftime("%B %d, %Y %I:%M %p")}) because your booking '
                        f'was cancelled for non-payment of the reservation deposit.'
                    )
                ns.notify_user(uid, f'Booking Violation - Strike #{new_strikes}', msg, 'violation')

                # Notify admins
                ns.notify_admins_inapp(
                    f'Booking Violation - Strike #{new_strikes}',
                    f'User #{uid} received Strike #{new_strikes} (Booking #{booking_id}). '
                    f'Suspension: {suspension_type}.',
                    'violation_admin'
                )
            except Exception as ne:
                print(f"[Violation] Notification error for user {uid}: {ne}")

        except Exception as err:
            print(f"[Violation] Error processing user {uid}: {err}")
        finally:
            if conn and not conn.closed:
                try: conn.close()
                except Exception: pass


def _send_payment_deadline_warnings():
    """
    Sends in-app notifications at 15-min and 5-min before the 30-min payment deadline.
    Called during check_and_update_unpaid_paymongo_bookings().
    """
    try:
        cur = get_cursor()
        cur.execute("""
            SELECT id, user_id, created_at FROM bookings
            WHERE payment_status IN ('Unpaid', 'Downpayment unpaid')
              AND status IN ('Pending', 'Pending Payment')
              AND paymongo_link_id IS NOT NULL AND paymongo_link_id != ''
              AND created_at > NOW() - INTERVAL '30 minutes'
              AND created_at < NOW() - INTERVAL '14 minutes'
        """)
        warn_rows = cur.fetchall() or []
        cur.close()

        for row in warn_rows:
            uid = row.get('user_id')
            bid = row.get('id')
            created = row.get('created_at')
            if not uid or not created:
                continue
            try:
                from datetime import datetime, timezone, timedelta
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                now_utc = datetime.now(timezone.utc)
                elapsed = (now_utc - created).total_seconds() / 60
                remaining = 30 - elapsed

                # 15-min warning: between 14 and 16 minutes elapsed
                if 14 <= elapsed < 16:
                    try:
                        from notifications import Notification_Service
                        Notification_Service().notify_user(
                            uid,
                            '⏰ 15 Minutes Left to Pay!',
                            f'Booking #{bid}: You have 15 minutes remaining to complete your reservation deposit payment. '
                            f'If not paid, your booking will be cancelled and a violation strike may be applied.',
                            'payment_warning'
                        )
                        print(f"[Violation] 15-min warning sent for booking #{bid} user #{uid}")
                    except Exception as ne:
                        print(f"[Violation] 15-min warning notification error: {ne}")

                # 5-min warning: between 24 and 26 minutes elapsed
                elif 24 <= elapsed < 26:
                    try:
                        from notifications import Notification_Service
                        Notification_Service().notify_user(
                            uid,
                            '🚨 FINAL WARNING: 5 Minutes Left!',
                            f'Booking #{bid}: Only 5 minutes remaining! Complete your reservation deposit NOW to avoid cancellation and a booking violation strike.',
                            'payment_warning_final'
                        )
                        print(f"[Violation] 5-min warning sent for booking #{bid} user #{uid}")
                    except Exception as ne:
                        print(f"[Violation] 5-min warning notification error: {ne}")
            except Exception:
                pass
    except Exception as e:
        print(f"[Violation] Payment deadline warning check error: {e}")
