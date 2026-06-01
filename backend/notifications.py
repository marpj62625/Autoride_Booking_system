import smtplib
import requests
import time
import sys
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_PORT, EMAIL_USER, EMAIL_PASS, SEMAPHORE_API_KEY, SEMAPHORE_SENDER_NAME
from database import get_cursor, commit_db


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def truncate_message(message: str, max_len: int = 320) -> str:
    """
    Truncates *message* to *max_len* characters.
    If the message exceeds *max_len*, it is cut to (max_len - 3) characters
    and '...' is appended so the total length equals exactly *max_len*.
    If the message is within the limit it is returned unchanged.
    """
    if len(message) > max_len:
        return message[:max_len - 3] + "..."
    return message


# ---------------------------------------------------------------------------
# Booking lifecycle compose functions
# ---------------------------------------------------------------------------

def compose_booking_created_sms(booking_id, brand, model, start_date, end_date, total_price) -> str:
    """SMS sent to customer when a new booking is created."""
    return (
        f"Your booking #{booking_id} for {brand} {model} from {start_date} to {end_date} "
        f"has been received. Total: PHP {total_price}. We'll review it shortly."
    )


def compose_booking_approved_sms(booking_id, brand, model, start_date) -> str:
    """SMS sent to customer when their booking is approved."""
    return (
        f"Good news! Booking #{booking_id} for {brand} {model} starting {start_date} "
        f"has been approved. Please proceed with pickup as scheduled."
    )


def compose_booking_rejected_sms(booking_id) -> str:
    """SMS sent to customer when their booking is rejected."""
    return (
        f"Booking #{booking_id} has been rejected. "
        f"Please contact our support team for assistance."
    )


def compose_customer_cancel_sms(booking_id, reason) -> str:
    """SMS sent to customer when they cancel their own booking."""
    return f"Your booking #{booking_id} has been cancelled. Reason: {reason}."


def compose_admin_cancel_sms(booking_id, reason) -> str:
    """SMS sent to customer when an admin cancels their booking."""
    return (
        f"Your booking #{booking_id} has been cancelled by our team. "
        f"Reason: {reason}. A refund will be initiated if applicable."
    )


def compose_pickup_sms(booking_id, brand, model, end_date) -> str:
    """SMS sent to customer when their vehicle is picked up."""
    return (
        f"Drive safely! Booking #{booking_id} for {brand} {model} is now active. "
        f"Return by {end_date}."
    )


def compose_completed_sms(booking_id) -> str:
    """SMS sent to customer when their booking is marked completed."""
    return (
        f"Thank you for choosing Autoride! Booking #{booking_id} is now completed. "
        f"We hope to see you again."
    )


def compose_modify_booking_sms(booking_id, new_start, new_end, new_total) -> str:
    """SMS sent to customer when their booking dates are modified."""
    return (
        f"Your booking #{booking_id} dates have been updated: {new_start} to {new_end}. "
        f"New total: PHP {new_total}."
    )


# ---------------------------------------------------------------------------
# Payment compose functions
# ---------------------------------------------------------------------------

def compose_full_payment_sms(booking_id, amount, method, reference_number) -> str:
    """SMS sent to customer when a full payment is confirmed."""
    return (
        f"Payment confirmed for booking #{booking_id}. "
        f"Amount: PHP {amount} via {method}. Ref: {reference_number}. "
        f"Your booking is confirmed."
    )


def compose_downpayment_sms(booking_id, amount_paid, balance_amount, reference_number) -> str:
    """SMS sent to customer when a downpayment is received."""
    return (
        f"Downpayment of PHP {amount_paid} received for booking #{booking_id}. "
        f"Ref: {reference_number}. Remaining balance: PHP {balance_amount}."
    )


def compose_balance_payment_sms(booking_id, amount, reference_number) -> str:
    """SMS sent to customer when their balance payment is received."""
    return (
        f"Balance payment of PHP {amount} received for booking #{booking_id}. "
        f"Ref: {reference_number}. Your booking is now fully paid."
    )


def compose_cash_paid_sms(booking_id, total_amount) -> str:
    """SMS sent to customer when an admin marks their booking as cash-paid."""
    return (
        f"Your booking #{booking_id} has been marked as fully paid. "
        f"Total amount: PHP {total_amount}. Thank you!"
    )


# ---------------------------------------------------------------------------
# Split payment compose functions
# ---------------------------------------------------------------------------

def compose_split_request_sms(booking_id, initiator_name, amount) -> str:
    """SMS sent to the split-payment partner when a split request is created."""
    return (
        f"{initiator_name} has requested a split payment for booking #{booking_id}. "
        f"Your share: PHP {amount}. Please pay via the Autoride app."
    )


def compose_split_paid_sms(booking_id, amount) -> str:
    """SMS sent to the booking initiator when their partner pays their split share."""
    return (
        f"Your split payment partner has paid PHP {amount} for booking #{booking_id}."
    )


# ---------------------------------------------------------------------------
# License verification compose functions
# ---------------------------------------------------------------------------

def compose_license_approved_sms() -> str:
    """SMS sent to customer when their driver's license is verified."""
    return (
        "Your driver's license has been verified! "
        "You can now book vehicles on Autoride."
    )


def compose_license_rejected_sms() -> str:
    """SMS sent to customer when their driver's license is rejected."""
    return (
        "Your driver's license was not approved. "
        "Please re-upload a valid document through the app."
    )


# ---------------------------------------------------------------------------
# Admin alert compose functions
# ---------------------------------------------------------------------------

def compose_admin_new_booking_sms(booking_id, customer_name, brand, model, start_date, end_date) -> str:
    """Admin alert SMS when a new booking is created."""
    return (
        f"New booking #{booking_id} from {customer_name} for {brand} {model}, "
        f"{start_date} to {end_date}. Review in admin panel."
    )


def compose_admin_payment_proof_sms(booking_id, customer_name, amount) -> str:
    """Admin alert SMS when a customer uploads a legacy payment proof."""
    return (
        f"Payment proof uploaded for booking #{booking_id} by {customer_name}. "
        f"Amount: PHP {amount}. Review in admin panel."
    )


# ---------------------------------------------------------------------------
# OTP compose function
# ---------------------------------------------------------------------------

def compose_otp_sms(otp_code) -> str:
    """SMS sent to a customer containing their one-time login password."""
    return (
        f"Your Autoride login code is {otp_code}. "
        f"It expires in 10 minutes. Do not share this code."
    )

def send_notification(user_id, subject, message):
    """Sends notification to user via Email and SMS."""
    try:
        cur = get_cursor()
        cur.execute("SELECT email, phone, full_name FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if not user:
            return False
            
        email = user['email']
        phone = user['phone']
        name = user['full_name']

        # 1. SEND EMAIL
        if email:
            try:
                body = f"Hello {name},\n\n{message}\n\nBest regards,\nAutoride System Team"
                msg = MIMEText(body)
                msg['Subject'] = subject
                msg['From'] = EMAIL_USER
                msg['To'] = email

                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(EMAIL_USER, EMAIL_PASS)
                    server.send_message(msg)
                print(f"DEBUG: Email sent to {email}")
            except Exception as e:
                print(f"FAILED TO SEND EMAIL: {e}")

        # 2. SEND SMS (SEMAPHORE)
        if phone and SEMAPHORE_API_KEY:
            try:
                sms_body = f"AUTORIDE: {message}"
                res = requests.post("https://api.semaphore.co/api/v4/messages", data={
                    'apikey': SEMAPHORE_API_KEY,
                    'number': phone,
                    'message': sms_body,
                    'sendername': SEMAPHORE_SENDER_NAME
                })
                print(f"DEBUG: SMS sent to {phone}. Status: {res.status_code}")
            except Exception as e:
                print(f"FAILED TO SEND SMS: {e}")
                
        return True
    except Exception as e:
        print(f"NOTIFICATION ERROR: {e}")
        return False
    finally:
        if 'cur' in locals(): cur.close()


# ---------------------------------------------------------------------------
# SMS_Service class
# ---------------------------------------------------------------------------

class SMS_Service:
    """
    Handles all SMS delivery for the AutorideSystem via the Semaphore API.
    Provides retry logic, delivery logging to sms_logs, opt-out support,
    and fan-out to multiple admin recipients.
    """

    def _log_sms(self, phone, recipient_type, recipient_id, message_body,
                 status, response_code=None, error_message=None):
        """
        Insert a row into sms_logs. Wrapped in try/except so a logging
        failure never crashes the send.
        """
        try:
            cur = get_cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO sms_logs
                        (recipient_phone, recipient_type, recipient_id,
                         message_body, status, semaphore_response_code, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (phone, recipient_type, recipient_id,
                     message_body, status, response_code, error_message)
                )
                commit_db()
            finally:
                cur.close()
        except Exception as log_err:
            print(f"SMS_Service: failed to write sms_logs entry: {log_err}", file=sys.stderr)

    def send_sms(self, phone: str, message: str, recipient_type: str,
                 recipient_id=None) -> bool:
        """
        Core delivery function.

        1. Prefixes message with 'AUTORIDE: ' and truncates to 320 chars.
        2. POSTs to Semaphore API.
        3. On non-2xx or network exception: logs 'retried', waits 2 s, retries once.
        4. Logs 'sent' on success, 'failed' after all retries exhausted.
        Returns True on success, False on failure.
        """
        prefixed = truncate_message("AUTORIDE: " + message)

        payload = {
            'apikey': SEMAPHORE_API_KEY,
            'number': phone,
            'message': prefixed,
            'sendername': SEMAPHORE_SENDER_NAME,
        }

        # --- First attempt ---
        first_response_code = None
        first_error = None
        try:
            resp = requests.post(
                "https://api.semaphore.co/api/v4/messages",
                data=payload
            )
            first_response_code = resp.status_code
            if resp.ok:
                # Success on first try
                self._log_sms(phone, recipient_type, recipient_id, prefixed,
                              'sent', first_response_code)
                return True
            # Non-2xx response
            first_error = f"HTTP {resp.status_code}: {resp.text}"
        except Exception as exc:
            first_error = str(exc)

        # --- Log 'retried' and wait ---
        self._log_sms(phone, recipient_type, recipient_id, prefixed,
                      'retried', first_response_code, first_error)
        time.sleep(2)

        # --- Retry attempt ---
        retry_response_code = None
        retry_error = None
        try:
            resp = requests.post(
                "https://api.semaphore.co/api/v4/messages",
                data=payload
            )
            retry_response_code = resp.status_code
            if resp.ok:
                self._log_sms(phone, recipient_type, recipient_id, prefixed,
                              'sent', retry_response_code)
                return True
            retry_error = f"HTTP {resp.status_code}: {resp.text}"
        except Exception as exc:
            retry_error = str(exc)

        # --- Both attempts failed ---
        self._log_sms(phone, recipient_type, recipient_id, prefixed,
                      'failed', retry_response_code, retry_error)
        return False

    def notify_customer(self, user_id: int, message: str,
                        is_transactional: bool = True) -> bool:
        """
        Looks up the user's phone_number and sms_opt_out from the users table.
        Skips the send if sms_opt_out=True and is_transactional=False.
        Calls send_sms() with recipient_type='customer'.
        Returns the result of send_sms(), or False if the send was skipped/failed.
        """
        try:
            cur = get_cursor()
            try:
                cur.execute(
                    "SELECT phone, sms_opt_out FROM users WHERE id = %s",
                    (user_id,)
                )
                user = cur.fetchone()
            finally:
                cur.close()

            if not user:
                print(
                    f"SMS_Service.notify_customer: user {user_id} not found",
                    file=sys.stderr
                )
                return False

            phone_number = user['phone']
            sms_opt_out = user['sms_opt_out']

            if not phone_number:
                print(
                    f"SMS_Service.notify_customer: user {user_id} has no phone number",
                    file=sys.stderr
                )
                return False

            if sms_opt_out and not is_transactional:
                # User has opted out of promotional messages
                return False

            return self.send_sms(phone_number, message,
                                 recipient_type='customer', recipient_id=user_id)

        except Exception as exc:
            print(
                f"SMS_Service.notify_customer: DB error for user {user_id}: {exc}",
                file=sys.stderr
            )
            return False

    def notify_admins(self, message: str) -> list:
        """
        Queries all active admins with a non-null phone number and sends
        each of them an SMS. Returns a list of booleans (one per admin).
        Returns [] if no active admins are found or on DB error.
        """
        try:
            cur = get_cursor()
            try:
                cur.execute(
                    "SELECT id, phone FROM admins WHERE is_active = TRUE AND phone IS NOT NULL"
                )
                admins = cur.fetchall()
            finally:
                cur.close()

            if not admins:
                return []

            results = []
            for admin in admins:
                result = self.send_sms(
                    admin['phone'], message,
                    recipient_type='admin', recipient_id=admin['id']
                )
                results.append(result)
            return results

        except Exception as exc:
            print(
                f"SMS_Service.notify_admins: DB error: {exc}",
                file=sys.stderr
            )
            return []

    def notify_phone(self, phone: str, message: str,
                     recipient_type: str, recipient_id=None) -> bool:
        """
        Sends an SMS to a known phone number directly (e.g. for OTP delivery
        where a user_id lookup is not needed). Delegates to send_sms().
        Returns the result of send_sms().
        """
        return self.send_sms(phone, message, recipient_type, recipient_id)


# Module-level singleton - route handlers can do:
#   from notifications import sms_service
sms_service = SMS_Service()


class Notification_Service:
    """
    Handles in-app notification delivery for the AutorideSystem.
    Inserts rows into the notifications table. Runs alongside SMS_Service.
    Failures are logged but never raised - route handlers are not affected.
    """

    def notify_user(self, user_id: int, title: str, message: str, notif_type: str) -> bool:
        """
        Inserts one notification row for a customer using a fresh DB connection.
        Also sends an FCM push notification if the user has a registered token.
        Returns True on success, False on failure.
        """
        try:
            import psycopg
            import os
            from config import SUPABASE_DB_URL
            from psycopg.rows import dict_row
            conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
            cur = conn.cursor(row_factory=dict_row)
            cur.execute(
                """
                INSERT INTO notifications (user_id, admin_id, title, message, type)
                VALUES (%s, NULL, %s, %s, %s)
                """,
                (user_id, title, message, notif_type)
            )
            conn.commit()
            cur.close()
            conn.close()
            # Also send FCM push
            try:
                global fcm_service
                if 'fcm_service' in globals():
                    fcm_service.notify_user_push(user_id, title, message)
            except Exception:
                pass
            return True
        except Exception as exc:
            print(
                f"Notification_Service.notify_user: failed for user {user_id}: {exc}",
                file=sys.stderr
            )
            return False

    def notify_admins_inapp(self, title: str, message: str, notif_type: str) -> list:
        """
        Finds all admin users and inserts one notification row per admin.
        Queries the users table (role = admin/super_admin) since that's where
        admin accounts are stored. Falls back to admins table if needed.
        Uses a single connection for all operations.
        """
        try:
            import psycopg
            from config import SUPABASE_DB_URL
            from psycopg.rows import dict_row

            conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
            try:
                cur = conn.cursor(row_factory=dict_row)

                # Try users table first (admin accounts stored here)
                admin_ids = []
                for query in [
                    "SELECT id FROM users WHERE role IN ('admin', 'super_admin')",
                    "SELECT id FROM admins WHERE is_active = TRUE",
                    "SELECT id FROM admins WHERE is_active IS NOT FALSE",
                    "SELECT id FROM admins",
                ]:
                    try:
                        conn.rollback()
                        cur.execute(query)
                        rows = cur.fetchall()
                        if rows:
                            admin_ids = [r['id'] for r in rows]
                            print(f"notify_admins_inapp: found {len(admin_ids)} admins via '{query[:40]}...'", file=sys.stderr)
                            break
                    except Exception as qe:
                        print(f"notify_admins_inapp: query failed '{query[:40]}': {qe}", file=sys.stderr)
                        continue

                if not admin_ids:
                    print("notify_admins_inapp: no admins found in any table", file=sys.stderr)
                    return []

                results = []
                for admin_id in admin_ids:
                    try:
                        conn.rollback()
                        cur.execute(
                            "INSERT INTO notifications (user_id, admin_id, title, message, type) VALUES (NULL, %s, %s, %s, %s)",
                            (admin_id, title, message, notif_type)
                        )
                        conn.commit()
                        print(f"notify_admins_inapp: stored for admin_id={admin_id}", file=sys.stderr)
                        results.append(True)
                    except Exception as exc:
                        conn.rollback()
                        print(f"notify_admins_inapp: insert failed for admin_id={admin_id}: {exc}", file=sys.stderr)
                        results.append(False)

                cur.close()
                return results
            finally:
                conn.close()

        except Exception as exc:
            print(f"Notification_Service.notify_admins_inapp: DB error: {exc}", file=sys.stderr)
            return []


notification_service = Notification_Service()


# ---------------------------------------------------------------------------
# FCM Push Notification Service (V1 API with Service Account)
# ---------------------------------------------------------------------------

class FCM_Service:
    """
    Sends native push notifications via Firebase Cloud Messaging V1 API.
    Uses a service account for OAuth2 authentication.
    """

    _access_token = None
    _token_expiry = 0

    def _get_access_token(self) -> str:
        """Get a valid OAuth2 access token, refreshing if expired."""
        import json
        import time

        now = time.time()
        if self._access_token and now < self._token_expiry - 60:
            return self._access_token

        try:
            import os

            # Load service account from environment variable (JSON string)
            sa_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
            if not sa_json:
                # Fallback: try local file (for local dev only, not committed to git)
                sa_path = os.path.join(os.path.dirname(__file__), 'firebase-service-account.json')
                if os.path.exists(sa_path):
                    with open(sa_path, 'r') as f:
                        sa = json.load(f)
                else:
                    print("FCM_Service: FIREBASE_SERVICE_ACCOUNT env var not set", file=sys.stderr)
                    return None
            else:
                sa = json.loads(sa_json)

            # Build JWT for service account
            import base64

            header = base64.urlsafe_b64encode(
                json.dumps({"alg": "RS256", "typ": "JWT"}).encode()
            ).rstrip(b'=').decode()

            iat = int(now)
            exp = iat + 3600
            payload = base64.urlsafe_b64encode(
                json.dumps({
                    "iss": sa['client_email'],
                    "scope": "https://www.googleapis.com/auth/firebase.messaging",
                    "aud": "https://oauth2.googleapis.com/token",
                    "iat": iat,
                    "exp": exp
                }).encode()
            ).rstrip(b'=').decode()

            signing_input = f"{header}.{payload}".encode()

            # Sign with private key
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding

            private_key = serialization.load_pem_private_key(
                sa['private_key'].encode(), password=None
            )
            signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
            sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()

            jwt_token = f"{header}.{payload}.{sig_b64}"

            # Exchange JWT for access token
            resp = requests.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                    'assertion': jwt_token
                },
                timeout=10
            )
            token_data = resp.json()
            self._access_token = token_data['access_token']
            self._token_expiry = now + token_data.get('expires_in', 3600)
            return self._access_token

        except Exception as exc:
            print(f"FCM_Service._get_access_token: failed: {exc}", file=sys.stderr)
            return None

    def send_push(self, fcm_token: str, title: str, body: str) -> bool:
        """
        Sends a push notification via FCM V1 API (service account) with
        legacy FCM HTTP API fallback if service account is unavailable.
        """
        # Try V1 API first (service account)
        try:
            access_token = self._get_access_token()
            if access_token:
                project_id = 'autoride-a1a32'
                resp = requests.post(
                    f'https://fcm.googleapis.com/v1/projects/{project_id}/messages:send',
                    headers={
                        'Authorization': f'Bearer {access_token}',
                        'Content-Type': 'application/json',
                    },
                    json={
                        'message': {
                            'token': fcm_token,
                            'notification': {'title': title, 'body': body},
                            'android': {
                                'priority': 'high',
                                'notification': {'sound': 'default', 'channel_id': 'autoride_notifications'}
                            },
                            'data': {'title': title, 'body': body}
                        }
                    },
                    timeout=10
                )
                if resp.ok:
                    return True
                print(f"FCM V1 failed ({resp.status_code}), trying legacy API", file=sys.stderr)
        except Exception as exc:
            print(f"FCM V1 error: {exc}, trying legacy API", file=sys.stderr)

        # Fallback: legacy FCM HTTP API using server key
        try:
            import os
            from config import FCM_SERVER_KEY
            server_key = os.environ.get('FCM_SERVER_KEY', FCM_SERVER_KEY)
            if not server_key:
                return False
            resp = requests.post(
                'https://fcm.googleapis.com/fcm/send',
                headers={
                    'Authorization': f'key={server_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'to': fcm_token,
                    'priority': 'high',
                    'notification': {
                        'title': title,
                        'body': body,
                        'sound': 'default',
                        'android_channel_id': 'autoride_notifications',
                    },
                    'data': {'title': title, 'body': body}
                },
                timeout=10
            )
            if not resp.ok:
                print(f"FCM legacy failed ({resp.status_code}): {resp.text}", file=sys.stderr)
            return resp.ok
        except Exception as exc:
            print(f"FCM legacy error: {exc}", file=sys.stderr)
            return False

    def notify_user_push(self, user_id: int, title: str, body: str) -> bool:
        """
        Looks up the user's FCM token from the users table and sends a push.
        Returns True on success, False if no token or send failed.
        """
        try:
            import psycopg
            from config import SUPABASE_DB_URL
            from psycopg.rows import dict_row
            conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
            cur = conn.cursor(row_factory=dict_row)
            cur.execute("SELECT fcm_token FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()

            if not row or not row.get('fcm_token'):
                return False

            return self.send_push(row['fcm_token'], title, body)
        except Exception as exc:
            print(f"FCM_Service.notify_user_push: DB error: {exc}", file=sys.stderr)
            return False


# Module-level singleton
fcm_service = FCM_Service()
