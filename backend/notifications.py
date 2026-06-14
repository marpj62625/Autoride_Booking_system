import smtplib
import sys
import requests
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_PORT, EMAIL_USER, EMAIL_PASS
from database import get_cursor, commit_db


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

        return True
    except Exception as e:
        print(f"NOTIFICATION ERROR: {e}")
        return False
    finally:
        if 'cur' in locals(): cur.close()


class Notification_Service:
    """
    Handles in-app notification delivery for the AutorideSystem.
    Inserts rows into the notifications table.
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

    def notify_admins_inapp(self, title: str, message: str, notif_type: str, **kwargs) -> list:
        """
        Finds all admin users and inserts one notification row per admin.
        Admin accounts are stored in the users table with role='admin'/'super_admin'.
        Inserts with user_id (not admin_id) so the FK constraint is satisfied and
        the GET /admin/notifications endpoint (which queries by user_id) can find them.
        Also sends a native FCM push notification to each admin's device.
        Always uses a dedicated separate DB connection to avoid interfering with
        any ongoing Flask request transaction.
        """
        try:
            import psycopg
            from config import SUPABASE_DB_URL
            from psycopg.rows import dict_row

            # Always use a separate, dedicated connection so we never interfere
            # with the outer Flask request's transaction.
            conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
            try:
                cur = conn.cursor(row_factory=dict_row)

                # Admin accounts live in the users table with role admin/super_admin
                cur.execute("SELECT id, fcm_token FROM users WHERE role IN ('admin', 'super_admin')")
                rows = cur.fetchall()
                admins = rows if rows else []

                if not admins:
                    print("notify_admins_inapp: no admin users found in users table", file=sys.stderr)
                    conn.close()
                    return []

                print(f"notify_admins_inapp: found {len(admins)} admin(s) in users table", file=sys.stderr)

                results = []
                for admin in admins:
                    uid = admin['id']
                    # Save in-app notification
                    try:
                        cur.execute(
                            "INSERT INTO notifications (user_id, admin_id, title, message, type) VALUES (%s, NULL, %s, %s, %s)",
                            (uid, title, message, notif_type)
                        )
                        conn.commit()
                        print(f"notify_admins_inapp: stored for user_id={uid}", file=sys.stderr)
                        results.append(True)
                    except Exception as exc:
                        conn.rollback()
                        print(f"notify_admins_inapp: insert failed for user_id={uid}: {exc}", file=sys.stderr)
                        results.append(False)

                    # Send native push notification if FCM token available
                    token = admin.get('fcm_token')
                    if token:
                        try:
                            fcm_service.send_push(token, title, message, channel_id='autoride_admin_high_priority', **kwargs)
                            print(f"notify_admins_inapp: push sent to user_id={uid}", file=sys.stderr)
                        except Exception as push_err:
                            print(f"notify_admins_inapp: push failed for user_id={uid}: {push_err}", file=sys.stderr)

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
                sa_json_clean = sa_json.strip()
                if sa_json_clean.startswith("'") and sa_json_clean.endswith("'"):
                    sa_json_clean = sa_json_clean[1:-1]
                elif sa_json_clean.startswith('"') and sa_json_clean.endswith('"') and not sa_json_clean.startswith('"{'):
                    sa_json_clean = sa_json_clean[1:-1]
                sa = json.loads(sa_json_clean)

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

            # Fix for Vercel: literal '\n' sequences in JSON env variables need to be actual newlines
            private_key_str = sa['private_key'].replace('\\n', '\n')
            
            private_key = serialization.load_pem_private_key(
                private_key_str.encode(), password=None
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

    def send_push(self, fcm_token: str, title: str, body: str, channel_id: str = 'autoride_high_priority', **kwargs) -> bool:
        """
        Sends a push notification via FCM V1 API (service account) with
        legacy FCM HTTP API fallback if service account is unavailable.
        """
        print(f"FCM_Service.send_push: Attempting to send push notification")
        print(f"  - Token: {fcm_token[:20]}...{fcm_token[-10:] if len(fcm_token) > 30 else fcm_token}")
        print(f"  - Title: {title}")
        print(f"  - Body: {body}")
        print(f"  - Channel: {channel_id}")
        
        # Build extra data dict for deep links
        extra_data = {
            'title': title,
            'body': body,
            'type': kwargs.get('type', ''),
            'booking_id': str(kwargs.get('booking_id', '')),
            'user_id': str(kwargs.get('user_id', ''))
        }
        
        # Try V1 API first (service account)
        try:
            access_token = self._get_access_token()
            if access_token:
                project_id = 'autoride-a1a32'
                print(f"FCM_Service: Trying V1 API with project {project_id}")
                resp = requests.post(
                    f'https://fcm.googleapis.com/v1/projects/{project_id}/messages:send',
                    headers={
                        'Authorization': f'Bearer {access_token}',
                        'Content-Type': 'application/json',
                    },
                    json={
                        'message': {
                            'token': fcm_token,
                            'android': {
                                'priority': 'high',
                                'notification': {
                                    'channel_id': channel_id,
                                    'sound': 'default',
                                    'notification_priority': 'PRIORITY_MAX',
                                    'default_sound': True,
                                    'default_vibrate_timings': True
                                }
                            },
                            'notification': {
                                'title': title,
                                'body': body
                            },
                            'data': extra_data
                        }
                    },
                    timeout=10
                )
                print(f"FCM V1 response: {resp.status_code} - {resp.text}")
                if resp.ok:
                    print("FCM V1: Push notification sent successfully!")
                    return True
                print(f"FCM V1 failed ({resp.status_code}), trying legacy API")
        except Exception as exc:
            print(f"FCM V1 error: {exc}, trying legacy API")

        # Fallback: legacy FCM HTTP API using server key
        try:
            import os
            from config import FCM_SERVER_KEY
            server_key = os.environ.get('FCM_SERVER_KEY', FCM_SERVER_KEY)
            
            if not server_key or server_key.strip() == '':
                print("FCM_Service: No server key configured - push notifications disabled")
                return False
                
            print(f"FCM_Service: Trying legacy API with server key: {server_key[:10]}...")
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
                        'android_channel_id': channel_id
                    },
                    'data': extra_data
                },
                timeout=10
            )
            print(f"FCM legacy response: {resp.status_code} - {resp.text}")
            if resp.ok:
                print("FCM Legacy: Push notification sent successfully!")
            else:
                print(f"FCM legacy failed ({resp.status_code}): {resp.text}")
            return resp.ok
        except Exception as exc:
            print(f"FCM legacy error: {exc}")
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
