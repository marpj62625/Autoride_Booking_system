from flask import Flask, request, jsonify, make_response
import bcrypt

from flask_cors import CORS

import typing

import os

from werkzeug.utils import secure_filename

# ─── Image upload validation ─────────────────────────────────────
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'heic', 'heif', 'bmp'}
ALLOWED_IMAGE_MIMES = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
    'image/webp', 'image/heic', 'image/heif', 'image/bmp'
}

def is_allowed_image(file_storage):
    """Return True if the FileStorage object is an allowed image type."""
    if not file_storage or not file_storage.filename:
        return False
    ext = file_storage.filename.rsplit('.', 1)[-1].lower() if '.' in file_storage.filename else ''
    mime = (file_storage.content_type or '').lower().split(';')[0].strip()
    return ext in ALLOWED_IMAGE_EXTENSIONS or mime in ALLOWED_IMAGE_MIMES

def reject_non_image(file_storage, field_name='file'):
    """Return a 400 JSON error if the file is not an allowed image, else None."""
    if file_storage and file_storage.filename and file_storage.filename != '':
        if not is_allowed_image(file_storage):
            from flask import jsonify
            return jsonify({'error': f'{field_name} must be an image file (jpg, png, gif, webp).'}), 400
    return None


from config import DEBUG, GOOGLE_CLIENT_ID, SUPABASE_URL, SUPABASE_KEY

from google.oauth2 import id_token

from google.auth.transport import requests as google_requests

import requests

from supabase import create_client, Client as SupabaseClient

from database import get_connection, release_connection, get_db, get_cursor, commit_db, init_db_helpers

from psycopg.rows import dict_row

import smtplib

from email.mime.text import MIMEText

from config import SMTP_SERVER, SMTP_PORT, EMAIL_USER, EMAIL_PASS

from datetime import datetime
import datetime as _dt
import decimal
import dataclasses
from flask.json.provider import DefaultJSONProvider


class ISODateJSONProvider(DefaultJSONProvider):
    """Custom JSON provider that serializes date/datetime as ISO 8601 strings
    instead of Flask 2.3's default RFC 7231 HTTP-date format (e.g. 'Mon, 01 Jun 2026 00:00:00 GMT').
    The HTTP-date format breaks JS Date parsing in the frontend."""

    def default(self, o):
        if isinstance(o, _dt.datetime):
            return o.isoformat()
        if isinstance(o, _dt.date):
            return o.isoformat()  # always 'YYYY-MM-DD'
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super().default(o)


app = Flask(__name__, 

            static_folder='../frontend', 

            static_url_path='')

app.json_provider_class = ISODateJSONProvider
app.json = ISODateJSONProvider(app)

app.url_map.strict_slashes = False

CORS(app, resources={r"/*": {

    "origins": "*",

    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],

    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]

}})

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum upload size is 16 MB.'}), 413

@app.errorhandler(Exception)
def handle_large_response(error):
    """Handle responses that might be too large for Vercel functions."""
    error_str = str(error)
    if len(error_str) > 1000:  # If error message is very long
        error_str = error_str[:500] + "... [truncated]"
    return jsonify({'error': error_str}), 500



@app.after_request

def add_header(response):

    response.headers['Access-Control-Allow-Origin'] = '*'

    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'

    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'

    return response



# Initialize database session management

init_db_helpers(app)



@app.route('/test/')

def test_connection():

    return jsonify({"status": "ok", "message": "Backend is reachable!"})



# Initialize Supabase Client for Storage

supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)



# Register Blueprints for modular routes

from routers.booking_routes import booking_bp

from routers.payment_routes import payment_bp

from routers.report_routes import report_bp

from routers.paymongo_routes import paymongo_bp

from booking_extension_routes import ext_bp
from routers.conflict_routes import conflict_bp

from utils.pdf_generator import generate_booking_pdf

import io

from flask import send_file



app.register_blueprint(booking_bp)

app.register_blueprint(payment_bp)

app.register_blueprint(report_bp)

app.register_blueprint(paymongo_bp)

app.register_blueprint(ext_bp)

app.register_blueprint(conflict_bp)


import threading
import time

def start_deadline_monitor():
    def monitor_loop():
        # Wait a short while on startup
        time.sleep(10)
        while True:
            try:
                from database import get_connection, release_connection
                conn = None
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = 'booking_conflicts'
                        )
                    """)
                    exists = cur.fetchone()[0]
                    if exists:
                        from services.extension_service import check_expired_deadlines
                        check_expired_deadlines()

                    # ── Check for no-show alerts (2hrs past pickup, still Confirmed/Approved, not yet notified) ──
                    try:
                        from datetime import datetime, timezone, timedelta
                        from psycopg.rows import dict_row
                        PH = timezone(timedelta(hours=8))
                        now_ph = datetime.now(tz=PH)

                        # We run a separate query with dict_row or manual fetch to get bookings
                        # Select Confirmed/Approved bookings where no_show_notified_at is null
                        cur.close()
                        cur = conn.cursor(row_factory=dict_row)
                        cur.execute("""
                            SELECT b.id, b.start_date, b.start_time, COALESCE(u.full_name, 'Unknown') as customer_name
                            FROM bookings b
                            LEFT JOIN users u ON b.user_id = u.id
                            WHERE b.status IN ('Confirmed', 'Approved')
                              AND b.no_show_notified_at IS NULL
                        """)
                        active_bookings = cur.fetchall()

                        for bk in active_bookings:
                            pickup_date = bk['start_date']
                            if hasattr(pickup_date, 'date'):
                                pickup_date = pickup_date.date()
                            pickup_time_str = bk.get('start_time') or '06:00'
                            # Handle time objects (not just strings)
                            if hasattr(pickup_time_str, 'strftime'):
                                pickup_time_str = pickup_time_str.strftime('%H:%M')
                            try:
                                ph_hour, ph_min = map(int, str(pickup_time_str)[:5].split(':'))
                            except Exception:
                                ph_hour, ph_min = 6, 0

                            pickup_dt = datetime(pickup_date.year, pickup_date.month, pickup_date.day, ph_hour, ph_min, tzinfo=PH)
                            deadline_dt = pickup_dt + timedelta(hours=2)

                            if now_ph >= deadline_dt:
                                # Trigger alert!
                                print(f"[MONITOR] Booking #{bk['id']} is 2 hours past pickup time. Alerting admins.")
                                from notifications import notification_service
                                try:
                                    notification_service.notify_admins_inapp(
                                        f"⚠️ No Show Alert: Booking #{bk['id']}",
                                        f"Customer '{bk['customer_name']}' has not shown up. Scheduled pickup was {pickup_date} at {pickup_time_str}. Please mark as No Show.",
                                        "admin_no_show",
                                        type="admin_no_show",
                                        booking_id=bk['id']
                                    )
                                except Exception as n_err:
                                    print(f"Failed to send admin no-show alert push: {n_err}")

                                # Update notified status
                                # Use a raw cursor or connection to execute UPDATE
                                cur.execute("UPDATE bookings SET no_show_notified_at = NOW() WHERE id = %s", (bk['id'],))
                                conn.commit()
                    except Exception as ns_err:
                        print("Deadline monitor thread no-show check failed:", ns_err)

                except Exception as e:
                    print("Deadline monitor thread table check failed:", e)
                finally:
                    if conn:
                        release_connection(conn)

            except Exception as e:
                print("Deadline monitor thread error:", e)
            time.sleep(600)  # Check every 10 minutes

    t = threading.Thread(target=monitor_loop, daemon=True)
    t.start()

start_deadline_monitor()


def migrate_settings_v2():

    """Ensures the settings table has the correct keys for the new business rules."""

    try:

        cur = get_cursor()

        # 1. Delete unwanted keys permanently

        cur.execute("DELETE FROM settings WHERE key IN ('tax_rate', 'service_fee', 'service_fee_percent', 'service_fee_fixed')")

        

        # 1.1 Migrate admins/users table (Location Lock)

        cur.execute("ALTER TABLE admins ADD COLUMN IF NOT EXISTS assigned_location VARCHAR(100)")

        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS assigned_location VARCHAR(100)")

        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'customer'")

        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified INT DEFAULT 0") # 0: Not Verified, 1: Pending, 2: Verified

        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS license_image_url TEXT")

        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS license_number VARCHAR(50)")

        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS license_expiry DATE")

        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS license_type VARCHAR(50)")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS force_logout_at TIMESTAMPTZ DEFAULT NULL")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS payment_status VARCHAR(50) DEFAULT 'Unpaid'")

        

        # New: Vehicle Inspection Table

        cur.execute("""

            CREATE TABLE IF NOT EXISTS vehicle_inspections (

                id SERIAL PRIMARY KEY,

                booking_id INT REFERENCES bookings(id),

                inspection_type VARCHAR(20), -- 'pickup' or 'return'

                photos JSONB, -- Array of photo URLs

                mileage INT,

                fuel_level VARCHAR(50),

                notes TEXT,

                inspector_id INT, -- Who did the check

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

            )

        """)

        

        # Create locations table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                province VARCHAR(100),
                municipality VARCHAR(100),
                barangay VARCHAR(100),
                delivery_fee NUMERIC(10,2) DEFAULT 0.00,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # Populate default locations
        default_locs = [
            ('San Pablo City, Laguna', 'Laguna', 'San Pablo City', '', 0.00),
            ('Tanauan/Sto. Tomas, Batangas', 'Batangas', 'Tanauan', 'Sto. Tomas', 0.00),
            ('Others (Subject to Admin Coordination)', 'Other', 'Other', 'Other', 0.00)
        ]
        for name, prov, muni, brgy, fee in default_locs:
            cur.execute("""
                INSERT INTO locations (name, province, municipality, barangay, delivery_fee)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (name, prov, muni, brgy, fee))

        # Add new columns to bookings table
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS delivery_fee NUMERIC(10,2) DEFAULT 0.00")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS points_redeemed INT DEFAULT 0")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS points_earned INT DEFAULT 0")

        # 2. Ensure new keys exist with default values
        new_configs = [
            ('mileage_limit', '250', 'Daily mileage limit in kilometers'),
            ('long_term_discount_days', '7', 'Minimum days for long-term discount'),
            ('long_term_discount_percent', '10', 'Long-term discount percentage'),
            ('loyalty_points_spend_ratio', '100', 'Spend amount in PHP required to earn 1 loyalty point'),
            ('loyalty_points_value', '0.1', 'Discount value in PHP of 1 loyalty point'),
            ('loyalty_max_discount_percent', '50', 'Maximum percentage of booking cost that can be covered by loyalty points discount')
        ]

        for key, val, desc in new_configs:
            cur.execute("""
                INSERT INTO settings (key, value, description) 
                VALUES (%s, %s, %s) 
                ON CONFLICT (key) DO NOTHING
            """, (key, val, desc))

        # 3. Force update the rental terms text if it is empty
        cur.execute("SELECT value FROM settings WHERE key = 'rental_terms'")
        existing_terms = cur.fetchone()
        if not existing_terms or not existing_terms['value']:
            terms_text = "Fuel Policy: Return the vehicle with the same fuel level as at pickup.\nMileage Rule: 250 km per day limit. Excess charged at ₱10/km.\nDriver Responsibility: You must be the primary driver with a valid verified license.\nLate Return: Penalty of ₱500 per hour for late returns.\nDamages: Any damages not covered by your selected insurance are your responsibility.\nCancellation: 20% reservation fee is non-refundable if cancelled less than 48 hours before pickup."
            cur.execute("UPDATE settings SET value = %s WHERE key = 'rental_terms'", (terms_text,))

        # 4. Create vehicle_expenses table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_expenses (
                id SERIAL PRIMARY KEY,
                vehicle_id INTEGER REFERENCES vehicles(id) ON DELETE CASCADE,
                expense_type VARCHAR(50) NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                expense_date DATE NOT NULL,
                description TEXT,
                proof_image_url TEXT,
                recorded_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        commit_db()


    except Exception as e:
        pass


    finally:

        if 'cur' in locals(): cur.close()



# Run migration on startup
try:
    with app.app_context():
        migrate_settings_v2()
except Exception as _e:
    pass



def migrate_payment_cancellation():

    """Adds columns for downpayments and customer cancellations."""

    try:

        cur = get_cursor()

        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS payment_type VARCHAR(50) DEFAULT 'Full'")

        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS amount_paid DECIMAL(10,2) DEFAULT 0")

        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS balance_amount DECIMAL(10,2) DEFAULT 0")

        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS cancellation_reason TEXT")

        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS cancelled_by VARCHAR(50)")

        commit_db()


    except Exception as e:
        pass


    finally:

        if 'cur' in locals(): cur.close()



try:
    with app.app_context():
        migrate_payment_cancellation()
except Exception as _e:
    pass


def migrate_notifications():

    """Creates the notifications table for in-app notifications."""

    try:

        cur = get_cursor()

        cur.execute("""

            CREATE TABLE IF NOT EXISTS notifications (

                id         BIGSERIAL PRIMARY KEY,

                user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,

                admin_id   INTEGER REFERENCES admins(id) ON DELETE CASCADE,

                title      TEXT NOT NULL,

                message    TEXT NOT NULL,

                type       TEXT NOT NULL,

                is_read    BOOLEAN NOT NULL DEFAULT FALSE,

                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

                CONSTRAINT chk_one_recipient CHECK (

                    (user_id IS NOT NULL AND admin_id IS NULL) OR

                    (user_id IS NULL AND admin_id IS NOT NULL)

                )

            )

        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications (user_id, created_at DESC)")

        cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_admin_id ON notifications (admin_id, created_at DESC)")

        commit_db()


    except Exception as e:
        pass


    finally:

        if 'cur' in locals(): cur.close()



try:
    with app.app_context():
        migrate_notifications()
except Exception as _e:
    pass

def migrate_chat():

    """Creates or migrates the chat_messages table for in-app admin-customer chat.
    If the old chatbot table exists (with user_message/bot_response columns), drops and recreates it.
    """

    try:

        cur = get_cursor()

        # Check if the table exists with the OLD schema (chatbot columns)
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='chat_messages' AND column_name='user_message'
        """)
        has_old_schema = cur.fetchone()

        if has_old_schema:
            # Old chatbot table - drop and recreate with new live-chat schema
            cur.execute("DROP TABLE IF EXISTS chat_messages CASCADE")
            commit_db()

        cur.execute("""

            CREATE TABLE IF NOT EXISTS chat_messages (

                id           BIGSERIAL PRIMARY KEY,

                sender_type  VARCHAR(10) NOT NULL CHECK (sender_type IN ('user','admin')),

                sender_id    INTEGER NOT NULL,

                receiver_type VARCHAR(10) NOT NULL CHECK (receiver_type IN ('user','admin')),

                receiver_id  INTEGER NOT NULL,

                message      TEXT NOT NULL,

                is_read      BOOLEAN NOT NULL DEFAULT FALSE,

                created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()

            )

        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_messages (sender_id, receiver_id, created_at DESC)")

        cur.execute("CREATE INDEX IF NOT EXISTS idx_chat_receiver ON chat_messages (receiver_type, receiver_id, is_read)")

        commit_db()


    except Exception as e:
        pass


    finally:

        if 'cur' in locals(): cur.close()



try:
    with app.app_context():
        migrate_chat()
except Exception as _e:
    pass

def migrate_fcm_tokens():
    """Adds fcm_token column to users and admins tables for push notifications."""
    try:
        cur = get_cursor()
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS fcm_token TEXT")
        cur.execute("ALTER TABLE admins ADD COLUMN IF NOT EXISTS fcm_token TEXT")
        commit_db()
    except Exception as e:
        pass
    finally:
        if 'cur' in locals(): cur.close()

try:
    with app.app_context():
        migrate_fcm_tokens()
except Exception as _e:
    pass


def migrate_extensions_v1():
    """Creates booking_extensions and booking_conflicts tables and adds extension columns to bookings."""
    try:
        cur = get_cursor()
        # 1. Ensure booking_extensions table exists
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
        cur.execute("ALTER TABLE booking_extensions ADD COLUMN IF NOT EXISTS approved_by_admin_id INTEGER")
        cur.execute("ALTER TABLE booking_extensions ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ")
        cur.execute("ALTER TABLE booking_extensions ADD COLUMN IF NOT EXISTS has_conflicts BOOLEAN DEFAULT FALSE")

        # 2. Add extension columns to bookings table
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS has_active_extension BOOLEAN DEFAULT FALSE")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS extension_count INT DEFAULT 0")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS is_conflict_affected BOOLEAN DEFAULT FALSE")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS conflict_id INT DEFAULT NULL")

        # 3. Create booking_conflicts table
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
        print("DEBUG: migrate_extensions_v1 completed successfully.")
    except Exception as e:
        print(f"DEBUG: migrate_extensions_v1 error (non-fatal): {e}")
    finally:
        if 'cur' in locals(): cur.close()

try:
    with app.app_context():
        migrate_extensions_v1()
except Exception as _e:
    pass


def migrate_license_details_table():
    """Creates the license_details table if it doesn't exist."""
    try:
        cur = get_cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS license_details (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) UNIQUE,
                full_name VARCHAR(255),
                date_of_birth DATE,
                license_number VARCHAR(100),
                expiry_date DATE,
                issuing_country_state VARCHAR(100),
                license_class VARCHAR(50),
                emergency_contact_name VARCHAR(255),
                emergency_contact_phone VARCHAR(50),
                emergency_contact_relationship VARCHAR(100),
                license_front_url TEXT,
                license_back_url TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        commit_db()
    except Exception as e:
        pass
    finally:
        if 'cur' in locals(): cur.close()

try:
    with app.app_context():
        migrate_license_details_table()
except Exception as _e:
    pass


def migrate_refund_columns():
    """Ensures refund tracking columns exist on bookings table."""
    try:
        cur = get_cursor()
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_amount NUMERIC(12,2)")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_method VARCHAR(100)")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_ref VARCHAR(200)")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_note TEXT")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMPTZ")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_proof_url TEXT")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_channel VARCHAR(50)")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_account_name VARCHAR(200)")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_account_number VARCHAR(100)")
        commit_db()
    except Exception as e:
        pass
    finally:
        if 'cur' in locals(): cur.close()

try:
    with app.app_context():
        migrate_refund_columns()
except Exception as _e:
    pass


def migrate_loyalty_points():
    """Ensures loyalty_points column exists on users table."""
    try:
        cur = get_cursor()
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS loyalty_points INTEGER DEFAULT 0")
        commit_db()
    except Exception as e:
        pass
    finally:
        if 'cur' in locals(): cur.close()

try:
    with app.app_context():
        migrate_loyalty_points()
except Exception as _e:
    pass


def migrate_google_auth_columns():
    """Ensures all columns required by the google_auth route exist in the users table.
    This replaces the disabled migrate_settings_v2() which had these columns commented out."""
    try:
        cur = get_cursor()
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id TEXT")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(50) DEFAULT 'email'")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS force_logout_at TIMESTAMPTZ DEFAULT NULL")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN DEFAULT FALSE")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_driver INT DEFAULT 0")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified INT DEFAULT 0")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_frozen BOOLEAN DEFAULT FALSE")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS freeze_reason TEXT")
        commit_db()
        print("[MIGRATION] google_auth_columns migration completed successfully")
    except Exception as e:
        print(f"[MIGRATION] google_auth_columns migration error (non-fatal): {e}")
    finally:
        if 'cur' in locals(): cur.close()


def migrate_no_show_column():
    """Ensures no_show_notified_at column exists in the bookings table for no show email/push alerts tracking."""
    try:
        cur = get_cursor()
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS no_show_notified_at TIMESTAMPTZ")
        commit_db()
        print("[MIGRATION] migrate_no_show_column completed successfully")
    except Exception as e:
        print(f"[MIGRATION] migrate_no_show_column error (non-fatal): {e}")
    finally:
        if 'cur' in locals(): cur.close()

try:
    with app.app_context():
        migrate_google_auth_columns()
        migrate_no_show_column()
except Exception as _e:
    pass




@app.before_request

def log_request_info():
    pass





def log_activity(admin_id, admin_name, action, target_type=None, target_id=None, details=None):

    ip = request.remote_addr

    try:

        cur = get_cursor()

        cur.execute("""

            INSERT INTO activity_logs (admin_id, admin_name, action, target_type, target_id, details, ip_address)

            VALUES (%s, %s, %s, %s, %s, %s, %s)

        """, (admin_id, admin_name, action, target_type, target_id, details, ip))

        commit_db()

    except Exception as e:

        print(f"FAILED TO LOG ACTIVITY: {e}")
        try:
            get_db().rollback()
        except:
            pass

    finally:

        if 'cur' in locals(): cur.close()



from flask import send_from_directory, render_template



@app.route('/admin_app/<path:filename>')

def serve_admin_app(filename):

    return send_from_directory('../admin_app', filename)



@app.route('/admin_mobile/<path:filename>')

def serve_admin_mobile(filename):

    return send_from_directory('../admin_mobile/www', filename)



@app.route('/privacy-policy')

def privacy_policy():

    """Serve the Privacy Policy page for Google Play Console compliance"""

    return render_template('privacy_policy.html')



UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



@app.route('/uploads/<path:filename>')

def serve_uploads(filename):

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



app.config['DEBUG'] = DEBUG



# Note: We now use db_pool from database.py instead of mysql.init_app



# Since we are using a connection pool, we need to manage connections per request

# To make this seamless with the existing code, we will store the connection in Flask's g object



# Database helpers are now in database.py

from database import get_db, get_cursor, commit_db



def is_gmail(email: str) -> bool:

    """Check if the email domain is precisely @gmail.com"""

    return email.lower().endswith('@gmail.com')



from notifications import notification_service



def send_verification_email(email: str, otp: str):

    """Sends a verification OTP via SMTP with terminal fallback."""

    subject = "Autoride Email Verification"

    body = f"Your Autoride verification code is: {otp}\n\nThis code is for your @gmail.com account verification."

    

    # TERMINAL FALLBACK (Log the code so the user can see it without real SMTP)

    print("\n" + "="*50)

    print(f"EMAIL VERIFICATION LOG")

    print(f"TO: {email}")

    print(f"CODE: {otp}")

    print("="*50 + "\n")



    try:

        msg = MIMEText(body)

        msg['Subject'] = subject

        msg['From'] = EMAIL_USER

        msg['To'] = email



        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:

            server.starttls()

            server.login(EMAIL_USER, EMAIL_PASS)

            server.send_message(msg)


    except Exception as e:
        pass




def send_receipt_email(email: str, details: dict):
    """Sends an HTML booking receipt email via SMTP."""
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText as MIMETextPart

    subject = 'Autoride Booking Receipt - Booking #' + str(details['id'])
    full_name = str(details.get('full_name', 'Customer'))
    brand = str(details.get('brand', ''))
    model_name = str(details.get('model', ''))
    start_date = str(details.get('start_date', ''))
    end_date = str(details.get('end_date', ''))
    booking_id = str(details['id'])
    total_price = float(details.get('total_price', 0) or 0)
    amount_paid = float(details.get('amount_paid', total_price) or total_price)
    base_price = float(details.get('base_price', 0) or 0)
    addon_price = float(details.get('addon_price', 0) or 0)
    insurance_price = float(details.get('insurance_price', 0) or 0)
    discount_amount = float(details.get('discount_amount', 0) or 0)
    balance_amount = float(details.get('balance_amount', 0) or 0)
    payment_type = str(details.get('payment_type', 'Full') or 'Full')
    insurance_text = str(details.get('insurance_type', 'Basic Protection') or 'Basic Protection')
    addons_raw = str(details.get('addons', '') or '')
    ref_num = str(details.get('reference_number', '') or 'N/A')
    method = str(details.get('method', 'N/A') or 'N/A')
    receipt_url = 'https://autoride-booking-system.vercel.app/api/bookings/' + booking_id + '/receipt'

    # Build breakdown rows for POS style receipt
    from datetime import datetime
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = (
        "<body style='margin:0;padding:20px;background:#f0f0f0;font-family:Arial,sans-serif;'>"
        "<div style='max-width:380px;margin:0 auto;background:#fff;padding:20px;color:#000;box-shadow:0 2px 10px rgba(0,0,0,0.1);'>"
        "<div style='text-align:center;margin-bottom:15px;'>"
        "<h2 style='margin:0;font-size:22px;letter-spacing:1px;text-transform:uppercase;'>AUTORIDE</h2>"
        "<p style='margin:2px 0 0;font-size:12px;'>Your ride, your way</p>"
        "</div>"
        
        "<div style='text-align:center;font-weight:bold;font-size:16px;margin:15px 0;border-top:1px dashed #000;border-bottom:1px dashed #000;padding:8px 0;letter-spacing:2px;'>"
        "INVOICE"
        "</div>"
        
        "<table width='100%' style='font-size:13px;margin-bottom:15px;line-height:1.4;'>"
        "<tr><td width='35%'>Booking No</td><td width='65%' style='text-align:right;'>" + booking_id + "</td></tr>"
        "<tr><td>Date</td><td style='text-align:right;'>" + now_str + "</td></tr>"
        "<tr><td>Customer</td><td style='text-align:right;'>" + full_name + "</td></tr>"
        "<tr><td>Rental Period</td><td style='text-align:right;'>" + start_date + " to " + end_date + "</td></tr>"
        "<tr><td>Vehicle</td><td style='text-align:right;'>" + brand + " " + model_name + "</td></tr>"
        "</table>"
        
        "<div style='border-top:1px dashed #000;margin:10px 0;'></div>"
        
        "<table width='100%' style='font-size:13px;margin-bottom:10px;'>"
        "<tr>"
        "<th style='text-align:left;padding-bottom:5px;width:65%;'>Item</th>"
        "<th style='text-align:center;padding-bottom:5px;width:10%;'>Qty</th>"
        "<th style='text-align:right;padding-bottom:5px;width:25%;'>Amount</th>"
        "</tr>"
        
        "<tr>"
        "<td style='padding:3px 0;'>Base Rental</td>"
        "<td style='text-align:center;padding:3px 0;'>1</td>"
        "<td style='text-align:right;padding:3px 0;'>" + '{:,.2f}'.format(base_price) + "</td>"
        "</tr>"
    )
    
    if addon_price > 0 and addons_raw and addons_raw != 'None':
        # Handle both JSON array format ["item"] and comma-separated format
        import json as _json
        try:
            parsed = _json.loads(addons_raw)
            addon_list = [str(a).strip() for a in parsed if str(a).strip()]
        except Exception:
            addon_list = [a.strip() for a in addons_raw.split(',') if a.strip()]
        for addon in addon_list:
            html += (
                "<tr>"
                "<td style='padding:3px 0;'>" + addon + "</td>"
                "<td style='text-align:center;padding:3px 0;'>1</td>"
                "<td style='text-align:right;padding:3px 0;'>" + '{:,.2f}'.format(addon_price / max(1, len(addon_list))) + "</td>"
                "</tr>"
            )
            
    if insurance_price > 0:
        html += (
            "<tr>"
            "<td style='padding:3px 0;'>Insurance</td>"
            "<td style='text-align:center;padding:3px 0;'>1</td>"
            "<td style='text-align:right;padding:3px 0;'>" + '{:,.2f}'.format(insurance_price) + "</td>"
            "</tr>"
        )
        
    if discount_amount > 0:
        html += (
            "<tr>"
            "<td style='padding:3px 0;'>Discount</td>"
            "<td style='text-align:center;padding:3px 0;'></td>"
            "<td style='text-align:right;padding:3px 0;'>-" + '{:,.2f}'.format(discount_amount) + "</td>"
            "</tr>"
        )
        
    html += (
        "</table>"
        "<div style='border-top:1px dashed #000;margin:10px 0;'></div>"
        
        "<table width='100%' style='font-size:14px;margin-bottom:15px;'>"
        "<tr>"
        "<td><strong>TOTAL (PHP)</strong></td>"
        "<td style='text-align:right;'><strong>" + '{:,.2f}'.format(total_price) + "</strong></td>"
        "</tr>"
    )
    
    if payment_type == 'Downpayment' and balance_amount > 0:
        html += (
            "<tr>"
            "<td style='padding-top:5px;font-size:13px;'>Paid Now (20%)</td>"
            "<td style='text-align:right;padding-top:5px;font-size:13px;'>" + '{:,.2f}'.format(amount_paid) + "</td>"
            "</tr>"
            "<tr>"
            "<td style='padding-top:3px;font-size:13px;'>Balance</td>"
            "<td style='text-align:right;padding-top:3px;font-size:13px;'>" + '{:,.2f}'.format(balance_amount) + "</td>"
            "</tr>"
        )
    else:
        html += (
            "<tr>"
            "<td style='padding-top:5px;font-size:13px;'>Amount Paid</td>"
            "<td style='text-align:right;padding-top:5px;font-size:13px;'>" + '{:,.2f}'.format(amount_paid) + "</td>"
            "</tr>"
        )
        
    html += (
        "</table>"
        "<div style='border-top:1px dashed #000;margin:10px 0;'></div>"
        
        "<table width='100%' style='font-size:13px;margin-bottom:20px;'>"
        "<tr><td style='width:40%;'>Payment Method</td><td style='text-align:right;'>" + method + "</td></tr>"
        "<tr><td style='width:40%;vertical-align:top;'>Reference No</td><td style='text-align:right;word-break:break-all;'>" + ref_num + "</td></tr>"
        "</table>"
        
        "<div style='text-align:center;margin:25px 0 15px;'>"
        "<p style='margin:0 0 5px;font-size:13px;'>Please Come Again</p>"
        "<p style='margin:0;font-size:11px;color:#555;'>autoride-booking-system.vercel.app</p>"
        "</div>"
        
        "<div style='text-align:center;margin-top:20px;'>"
        "<a href='" + receipt_url + "' style='display:inline-block;border:1px solid #000;color:#000;text-decoration:none;padding:8px 15px;font-size:12px;text-transform:uppercase;'>Download PDF</a>"
        "</div>"
        
        "</div>"
        "</body>"
    )

    print('RECEIPT EMAIL - TO: ' + email + ' BOOKING: #' + booking_id)
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = email
        msg.attach(MIMETextPart(html, 'html', 'utf-8'))
        smtp_port = int(SMTP_PORT) if SMTP_PORT else 587
        with smtplib.SMTP(SMTP_SERVER, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
    except Exception as e:
        pass

@app.route("/")

def home():

    return "Autoride backend running"



@app.route('/register', methods=['POST'])

def register():

    # Handle both JSON and Multipart

    if request.is_json:

        data = request.json

        first_name = data.get('first_name')

        middle_name = data.get('middle_name', '')

        last_name = data.get('last_name')

        email = data.get('email')

        password = data.get('password')

    else:

        first_name = request.form.get('first_name')

        middle_name = request.form.get('middle_name', '')

        last_name = request.form.get('last_name')

        email = request.form.get('email')

        password = request.form.get('password')

    

    if not email or not is_gmail(email):

        return jsonify({"error": "Only @gmail.com emails are allowed for registration."}), 400

    if not first_name or not first_name.strip():

        return jsonify({"error": "First name is required."}), 400



    try:

        cur = get_cursor()

        cur.execute("SELECT id FROM users WHERE email=%s", (email,))

        if cur.fetchone():

            return jsonify({"error": "Email already registered"}), 409



        # Handle optional license file during registration

        license_url = None

        is_verified = 0

        if 'license' in request.files:

            file = request.files['license']

            if file.filename != '':

                _img_err = reject_non_image(file, 'License'); 

                if _img_err: return _img_err

                filename = secure_filename(f"reg_license_{int(datetime.now().timestamp())}_{file.filename}")

                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                file.save(filepath)

                license_url = f"/uploads/{filename}"

                is_verified = 1 # Pending



        import random

        otp = str(random.randint(100000, 999999))
        temp_email_otps[email] = otp

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cur.execute("""
            INSERT INTO users(first_name, middle_name, last_name, email, password, is_email_verified, is_verified, license_image_url, role)
            VALUES(%s, %s, %s, %s, %s, False, %s, %s, 'customer')
            RETURNING id
        """, (first_name, middle_name, last_name, email, hashed_pw, is_verified, license_url))

        

        user_id = cur.fetchone()['id']

        commit_db()

        send_verification_email(email, otp)



        return jsonify({

            "message": "Registration successful. Please verify your email.",

            "user_id": user_id,

            "verification_required": True

        }), 201

    except Exception as e:
        import traceback as _tb
        err_detail = _tb.format_exc()
        print(f"ERROR in admin_login: {err_detail}")
        return jsonify({"error": str(e), "detail": err_detail[-500:]}), 500



@app.route('/health')
@app.route('/health/')
def health_check():
    """Quick DB connectivity test - call /api/health to debug Vercel"""
    try:
        cur = get_cursor()
        cur.execute("SELECT 1 AS ok")
        row = cur.fetchone()
        cur.close()
        return jsonify({"status": "ok", "db": "connected", "row": dict(row) if row else None}), 200
    except Exception as e:
        import traceback as _tb
        return jsonify({"status": "error", "db": str(e), "detail": _tb.format_exc()[-1000:]}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/user/forgot-password', methods=['POST'])
def user_forgot_password():
    """Forgot password endpoint for customers. Generates a temporary password and emails it."""
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'Email is required'}), 400
        
    try:
        cur = get_cursor()
        cur.execute("SELECT id, full_name, auth_provider, password FROM users WHERE LOWER(email) = %s", (email,))
        user = cur.fetchone()
        
        if not user:
            return jsonify({'error': 'Email address not found'}), 404
            
        if user.get('auth_provider') == 'google' and not user.get('password'):
            return jsonify({'error': 'This email is registered using Google Sign-In. Please log in using Google.'}), 400

        # Generate random 8-character temporary password
        import string
        import random
        import bcrypt
        
        temp_chars = string.ascii_letters + string.digits
        temp_password = ''.join(random.choice(temp_chars) for _ in range(8))
        
        # Hash temporary password
        hashed_pw = bcrypt.hashpw(temp_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update user's password in database
        cur.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_pw, user['id']))
        commit_db()
        
        # Send temporary password via email using notifications.py SMTP logic
        try:
            from notifications import send_notification
            subject = "Autoride Password Reset"
            message = f"Hello {user['full_name']},\n\nWe received a request to reset your password. Your new temporary password is:\n\n{temp_password}\n\nPlease use this temporary password to log in and change your password in your Profile Settings immediately."
            send_notification(user['id'], subject, message)
            print(f"Forgot password email sent to {email}")
        except Exception as email_err:
            print(f"Failed to send forgot password email: {email_err}")
            return jsonify({'error': 'Failed to send temporary password email. Please try again later.'}), 500
            
        return jsonify({'message': 'Temporary password sent successfully! Please check your email inbox.'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()



@app.route('/login', methods=['POST'])

def login():

    data = request.json

    email = data.get('email')

    password = data.get('password')

    

    if not email or not password:

        return jsonify({"error": "Missing credentials"}), 400



    # 1. Domain Restriction (@gmail.com only)

    if not is_gmail(email):

        return jsonify({"error": "Only @gmail.com accounts can sign in."}), 400



    try:

        cur = get_cursor()

        cur.execute("SELECT id, full_name, email, password, is_frozen, freeze_reason, is_email_verified, is_verified FROM users WHERE email=%s", (email,))
        user_row = cur.fetchone()
        user = None
        if user_row:
            stored = user_row['password'] or ''
            # Support legacy plain-text passwords (auto-upgrade on next login)
            try:
                pw_ok = bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8'))
            except Exception:
                pw_ok = (stored == password)
                if pw_ok:
                    # Upgrade to bcrypt hash
                    new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    cur.execute("UPDATE users SET password=%s WHERE id=%s", (new_hash, user_row['id']))
                    commit_db()
            if pw_ok:
                user = user_row
                try:
                    cur.execute("UPDATE users SET force_logout_at = NULL WHERE id = %s", (user['id'],))
                    commit_db()
                except Exception as fle:
                    print(f"WARN login: reset force_logout_at failed: {fle}")

        

        if user:

            # Check Email Verification Status

            if not user.get('is_email_verified'):

                return jsonify({

                    "error": "Email not verified", 

                    "verification_required": True,

                    "email": email

                }), 403



            if user.get('is_frozen'):

                reason = user.get('freeze_reason') or 'Your account has been suspended by an administrator.'

                return jsonify({"error": "Account Frozen", "reason": reason}), 403

            # Block login if license is pending verification
            if user.get('is_verified') == 1:
                return jsonify({
                    "error": "License pending verification",
                    "reason": "Your license is currently under review. Please wait for admin verification before logging in."
                }), 403
                
            return jsonify({

                "message": "login success", 

                "user_id": user['id'], 

                "full_name": user['full_name'],

                "is_verified": user.get('is_verified', 0)

            }), 200

        else:

            return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/admin/verify-action', methods=['POST'])

def admin_verify_user():

    data = request.json

    user_id = data.get('user_id')

    status = data.get('status') # 2 for Verified, 0 for Rejected

    admin_id = data.get('admin_id')

    

    if not user_id or status is None:

        return jsonify({"error": "Missing parameters"}), 400

    # Ensure correct types
    try:
        user_id = int(user_id)
        status  = int(status)
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid parameter types: {e}"}), 400

    # Use a fresh direct connection - bypasses g.db_conn / PgBouncer state issues
    import psycopg as _psycopg
    from config import SUPABASE_DB_URL as _DB_URL
    from psycopg.rows import dict_row as _dict_row
    conn = None
    try:
        conn = _psycopg.connect(conninfo=_DB_URL)
        cur = conn.cursor(row_factory=_dict_row)

        cur.execute("UPDATE users SET is_verified = %s WHERE id = %s", (status, user_id))
        rows_updated = cur.rowcount

        # Verify before commit
        cur.execute("SELECT is_verified FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()

        conn.commit()

        # Verify after commit on same connection
        cur.execute("SELECT is_verified FROM users WHERE id = %s", (user_id,))
        row2 = cur.fetchone()

        cur.close()
        conn.close()
        conn = None

        # Log activity
        if admin_id:
            try:
                log_cur = get_cursor()
                log_cur.execute("SELECT username FROM admins WHERE id = %s", (admin_id,))
                admin_row = log_cur.fetchone()
                admin_name = admin_row['username'] if admin_row else f"Admin {admin_id}"
                action_text = "Approved User Verification" if status == 2 else "Rejected User Verification"
                log_activity(admin_id, admin_name, action_text, "user", user_id)
            except Exception as log_err:
                print(f"WARN verify-action: activity log failed: {log_err}")

        # Send notifications
        if status == 2:
            notification_service.notify_user(
                user_id,
                "License Approved",
                "Your driver's license has been verified! You can now book vehicles on Autoride.",
                'license_approved'
            )
            # Stamp force_logout_at so the customer app force-logs out and re-logs in with fresh status
            try:
                import psycopg as _psycopg2
                conn2 = _psycopg2.connect(conninfo=_DB_URL)
                cur2 = conn2.cursor()
                cur2.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS force_logout_at TIMESTAMPTZ DEFAULT NULL")
                cur2.execute("UPDATE users SET force_logout_at = NOW() WHERE id = %s", (user_id,))
                conn2.commit()
                cur2.close()
                conn2.close()
            except Exception as fle:
                print(f"WARN: force_logout_at stamp failed: {fle}")
        elif status == 0:
            notification_service.notify_user(
                user_id,
                "License Rejected",
                "Your driver's license was not approved. Please re-upload a valid document through the app.",
                'license_rejected'
            )

        return jsonify({"message": f"User status updated to {status}", "rows_updated": rows_updated}), 200

    except Exception as e:
        print(f"ERROR verify-action: {e}")
        if conn:
            try: conn.rollback()
            except Exception: pass
            try: conn.close()
            except Exception: pass

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/user/verify-status', methods=['GET'])

def check_verify_status():

    user_id = request.args.get('user_id')

    if not user_id: return jsonify({"error": "Missing user_id"}), 400

    try:

        cur = get_cursor()

        # Force read from primary (not replica) to avoid stale reads after admin approval
        cur.execute("SET TRANSACTION READ WRITE")

        cur.execute("SELECT is_verified, license_image_url, force_logout_at FROM users WHERE id = %s", (user_id,))

        user = cur.fetchone()

        if not user: return jsonify({"error": "User not found"}), 404

        result = dict(user)
        if result.get('force_logout_at'):
            result['force_logout_at'] = result['force_logout_at'].isoformat()
        return jsonify(result), 200

    except Exception as e: return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/user/upload-license', methods=['POST'])

def upload_license():

    user_id = request.form.get('user_id')

    if not user_id: return jsonify({"error": "User ID required"}), 400

    

    if 'license' not in request.files:

        return jsonify({"error": "No file uploaded"}), 400

        

    file = request.files['license']

    if file.filename == '':

        return jsonify({"error": "No selected file"}), 400

        

    try:

        cur = get_cursor()

        filename = f"license_{user_id}_{int(datetime.now().timestamp())}.jpg"

        

        # Upload to Supabase Storage instead of local disk

        file_data = file.read()

        try:

            res = supabase.storage.from_('uploads').upload(

                path=filename,

                file=file_data,

                file_options={"content-type": "image/jpeg", "upsert": "true"}

            )

        except Exception as storage_exc:

            print(f"[upload_license] Supabase storage error for user {user_id}: {storage_exc}")

            return jsonify({"error": "Failed to upload license image. Please try again."}), 500

        

        # Get public URL

        url = supabase.storage.from_('uploads').get_public_url(filename)

        

        # Check previous is_verified status to see if it is a re-upload after rejection
        cur.execute("SELECT is_verified, license_image_url FROM users WHERE id = %s", (user_id,))
        user_row = cur.fetchone()
        prev_is_verified = user_row['is_verified'] if user_row else 0
        has_existing_license = bool(user_row['license_image_url']) if user_row else False
        is_reupload = (prev_is_verified == 0 and has_existing_license)

        # is_verified = 1 means 'Pending Review'
        cur.execute("UPDATE users SET license_image_url = %s, is_verified = 1 WHERE id = %s", (url, user_id))
        commit_db()

        # Notify admins
        try:
            cur.execute("SELECT full_name FROM users WHERE id = %s", (user_id,))
            u = cur.fetchone()
            uname = u['full_name'] if u else f'User #{user_id}'
            
            if is_reupload:
                title = "Re-uploaded License for Review"
                msg = f"⚠️ RE-UPLOAD: {uname} has re-uploaded their driver's license after rejection. Awaiting review."
            else:
                title = "License Uploaded for Review"
                msg = f"{uname} has uploaded a driver's license and is awaiting verification."

            notification_service.notify_admins_inapp(
                title,
                msg,
                'admin_license_upload',
                type='license',
                user_id=user_id
            )
        except Exception as notif_err:
            print(f"License upload admin notification error: {notif_err}")

        return jsonify({"message": "License uploaded for verification", "url": url}), 200

    except Exception as e:

        import traceback as _tb
        print(f"[upload_license] Unexpected error: {_tb.format_exc()}")

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/admin/users', methods=['GET'])

@app.route('/admin/pending-verifications', methods=['GET'])

def admin_list_users():

    status = request.args.get('status')

    if 'pending-verifications' in request.path:

        status = 'pending'

        


    try:

        cur = get_cursor()

        if status == 'pending':

            # is_verified = 1 is Pending

            cur.execute("""
                SELECT u.id, COALESCE(ld.full_name, u.full_name) AS full_name, u.email, u.phone,
                       COALESCE(ld.license_front_url, u.license_image_url) AS license_image,
                       COALESCE(ld.license_number, u.license_number) AS license_number,
                       COALESCE(CAST(ld.expiry_date AS TEXT), CAST(u.license_expiry AS TEXT)) AS license_expiry,
                       COALESCE(ld.license_class, u.license_type) AS license_type,
                       ld.license_back_url, ld.issuing_country_state, 
                       CAST(ld.date_of_birth AS TEXT) AS date_of_birth, ld.emergency_contact_name, 
                       ld.emergency_contact_phone, ld.emergency_contact_relationship,
                       u.is_verified
                FROM users u
                LEFT JOIN license_details ld ON u.id = ld.user_id
                WHERE u.is_verified = 1
                ORDER BY u.id DESC
            """)

        else:

            cur.execute("""
                SELECT u.id, COALESCE(ld.full_name, u.full_name) AS full_name, u.email, u.phone,
                       COALESCE(ld.license_front_url, u.license_image_url) AS license_image,
                       COALESCE(ld.license_number, u.license_number) AS license_number,
                       COALESCE(CAST(ld.expiry_date AS TEXT), CAST(u.license_expiry AS TEXT)) AS license_expiry,
                       COALESCE(ld.license_class, u.license_type) AS license_type,
                       ld.license_back_url, ld.issuing_country_state, 
                       CAST(ld.date_of_birth AS TEXT) AS date_of_birth, ld.emergency_contact_name, 
                       ld.emergency_contact_phone, ld.emergency_contact_relationship,
                       u.is_verified
                FROM users u
                LEFT JOIN license_details ld ON u.id = ld.user_id
                ORDER BY u.id DESC
            """)

        

        users = cur.fetchall()

        result = []
        for u in users:
            d = dict(u)
            if d.get('license_expiry'):
                d['license_expiry'] = str(d['license_expiry']).split(' ')[0]
            if d.get('date_of_birth'):
                d['date_of_birth'] = str(d['date_of_birth']).split(' ')[0]
            result.append(d)


        return jsonify(result), 200

    except Exception as e:

        print(f"ERROR pending-verifications: {e}")

        try:
            get_db().rollback()
        except Exception:
            pass

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()


# ??? ADMIN USER MANAGEMENT ENDPOINTS ???????????????????????????????????????

@app.route('/admin/users/list', methods=['GET'])
def admin_users_list():
    """Full user list with all fields for admin management."""
    try:
        cur = get_cursor()
        cur.execute("""
            SELECT id, full_name, email, phone, is_verified, is_frozen,
                   freeze_reason, loyalty_points, created_at,
                   profile_picture, auth_provider
            FROM users
            ORDER BY created_at DESC
        """)
        users = cur.fetchall()
        result = []
        for u in users:
            d = dict(u)
            d['is_verified'] = int(d.get('is_verified') or 0)
            d['is_frozen'] = bool(d.get('is_frozen'))
            d['loyalty_points'] = int(d.get('loyalty_points') or 0)
            if d.get('created_at'):
                d['created_at'] = str(d['created_at'])
            result.append(d)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/users/<int:user_id>', methods=['GET'])
def admin_user_detail(user_id):
    """Get full user detail including booking count."""
    try:
        cur = get_cursor()
        cur.execute("""
            SELECT id, full_name, email, phone, is_verified, is_frozen,
                   freeze_reason, loyalty_points, created_at,
                   profile_picture, auth_provider, province, municipality, barangay,
                   license_image_url, license_number, license_expiry, license_type
            FROM users WHERE id = %s
        """, (user_id,))
        user = cur.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404
        d = dict(user)
        d['is_verified'] = int(d.get('is_verified') or 0)
        d['is_frozen'] = bool(d.get('is_frozen'))
        d['loyalty_points'] = int(d.get('loyalty_points') or 0)
        if d.get('created_at'):
            d['created_at'] = str(d['created_at'])
        if d.get('license_expiry'):
            d['license_expiry'] = str(d['license_expiry'])
        # Booking stats
        cur.execute("SELECT COUNT(*) as total FROM bookings WHERE user_id = %s", (user_id,))
        d['total_bookings'] = (cur.fetchone() or {}).get('total', 0)
        cur.execute("SELECT COUNT(*) as completed FROM bookings WHERE user_id = %s AND status = 'Completed'", (user_id,))
        d['completed_bookings'] = (cur.fetchone() or {}).get('completed', 0)
        cur.execute("SELECT COALESCE(SUM(total_price),0) as spent FROM bookings WHERE user_id = %s AND status = 'Completed'", (user_id,))
        d['total_spent'] = float((cur.fetchone() or {}).get('spent', 0))
        return jsonify(d), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/users/<int:user_id>/freeze', methods=['POST'])
def admin_freeze_user(user_id):
    """Freeze or unfreeze a user account."""
    data = request.get_json(silent=True) or {}
    freeze = data.get('freeze', True)
    reason = data.get('reason', '')
    try:
        cur = get_cursor()
        cur.execute(
            "UPDATE users SET is_frozen = %s, freeze_reason = %s WHERE id = %s",
            (freeze, reason if freeze else None, user_id)
        )
        commit_db()
        action = 'frozen' if freeze else 'unfrozen'
        return jsonify({"message": f"User account {action} successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/users/<int:user_id>/edit', methods=['PUT'])
def admin_edit_user(user_id):
    """Edit user basic info."""
    data = request.get_json(silent=True) or {}
    first_name = data.get('first_name', '').strip()
    middle_name = data.get('middle_name', '').strip()
    last_name = data.get('last_name', '').strip()
    phone = data.get('phone', '').strip()
    if not first_name or not last_name:
        return jsonify({"error": "First name and last name are required"}), 400
    try:
        cur = get_cursor()
        cur.execute(
            "UPDATE users SET first_name = %s, middle_name = %s, last_name = %s, phone = %s WHERE id = %s",
            (first_name, middle_name or None, last_name, phone or None, user_id)
        )
        commit_db()
        return jsonify({"message": "User updated successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/users/<int:user_id>/loyalty', methods=['PUT'])
def admin_set_loyalty(user_id):
    """Set loyalty points for a user."""
    data = request.get_json(silent=True) or {}
    points = data.get('points')
    if points is None or not str(points).lstrip('-').isdigit():
        return jsonify({"error": "Valid points value required"}), 400
    try:
        cur = get_cursor()
        cur.execute("UPDATE users SET loyalty_points = %s WHERE id = %s", (int(points), user_id))
        commit_db()
        return jsonify({"message": f"Loyalty points set to {points}."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
def admin_reset_password(user_id):
    """Reset user password to a new value."""
    data = request.get_json(silent=True) or {}
    new_password = data.get('new_password', '').strip()
    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        cur = get_cursor()
        cur.execute("UPDATE users SET password = %s WHERE id = %s", (hashed, user_id))
        commit_db()
        return jsonify({"message": "Password reset successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    """Permanently delete a user account."""
    try:
        cur = get_cursor()
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        commit_db()
        return jsonify({"message": "User deleted successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/users/export', methods=['GET'])
def admin_export_users():
    """Export users as CSV."""
    import csv, io
    try:
        cur = get_cursor()
        cur.execute("""
            SELECT id, full_name, email, phone, is_verified, is_frozen,
                   loyalty_points, created_at
            FROM users ORDER BY created_at DESC
        """)
        users = cur.fetchall()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Full Name', 'Email', 'Phone', 'Verified', 'Frozen', 'Loyalty Points', 'Joined'])
        for u in users:
            d = dict(u)
            writer.writerow([
                d['id'], d['full_name'], d['email'], d.get('phone', ''),
                'Yes' if d.get('is_verified') else 'No',
                'Yes' if d.get('is_frozen') else 'No',
                d.get('loyalty_points', 0),
                str(d.get('created_at', ''))
            ])
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=users_export.csv'}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ??? END ADMIN USER MANAGEMENT ??????????????????????????????????????????????



@app.route('/user/points', methods=['GET'])

def get_user_points():

    user_id = request.args.get('user_id')

    if not user_id:

        return jsonify({"error": "User ID required"}), 400

    try:

        cur = get_cursor()

        cur.execute("SELECT loyalty_points FROM users WHERE id = %s", (user_id,))

        user = cur.fetchone()

        return jsonify({"points": user['loyalty_points'] if user else 0}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()




temp_email_otps = {}



@app.route('/auth/verify-email', methods=['POST'])

def verify_email():

    """Verify the 6-digit OTP sent to the user's gmail."""

    data = request.json

    email = data.get('email')

    otp = data.get('otp')

    

    if not email or not otp:

        return jsonify({"error": "Email and OTP are required"}), 400

    

    if temp_email_otps.get(email) == str(otp):

        try:

            cur = get_cursor()
            cur.execute("UPDATE users SET is_email_verified = True, force_logout_at = NULL WHERE email = %s RETURNING id, full_name, is_driver", (email,))
            user = cur.fetchone()
            commit_db()

            del temp_email_otps[email]

            

            if user:

                return jsonify({

                    "message": "Email verified successfully!",

                    "user_id": user['id'],

                    "full_name": user['full_name'],

                    "is_driver": user['is_driver']

                }), 200

            else:

                return jsonify({"message": "Email verified successfully!"}), 200

        except Exception as e:

            return jsonify({"error": str(e)}), 500

    else:

        return jsonify({"error": "Invalid or expired verification code"}), 400



@app.route('/auth/google', methods=['POST'])

def google_auth():

    data = request.json

    print(f"[GOOGLE_AUTH] Received data keys: {list(data.keys()) if data else 'None'}")

    print(f"[GOOGLE_AUTH] credential: {data.get('credential')[:50] if data and data.get('credential') else 'None'}...")

    print(f"[GOOGLE_AUTH] id_token: {data.get('id_token')[:50] if data and data.get('id_token') else 'None'}...")

    

    # Accept both 'credential' and 'id_token' for compatibility

    credential = data.get('credential') or data.get('id_token')

    is_driver = 1 if data.get('is_driver') else 0

    email = data.get('email')

    name = data.get('name')

    

    if not credential:

        print(f"[GOOGLE_AUTH] ERROR: No credential found! Data: {data}")

        return jsonify({"error": "No credential provided"}), 400



    try:

        # Decode the token without verification to see what's in it

        import base64

        import json

        

        # Split the JWT token (format: header.payload.signature)

        parts = credential.split('.')

        if len(parts) != 3:

            # Not a JWT - could be an OAuth2 access token from web flow.
            # In this case, email and name must be provided directly by the frontend
            # (which already verified them via Google's userinfo endpoint).
            if email and '@' in email:
                print(f"[GOOGLE_AUTH] Access token flow - using provided email: {email}")
                idinfo = {
                    'email': email,
                    'name': name or 'Google User',
                    'sub': 'oauth2_' + email.replace('@', '_').replace('.', '_'),
                    'email_verified': True
                }
            else:
                print(f"[GOOGLE_AUTH] Invalid token format and no email provided")
                return jsonify({"error": "Invalid token format"}), 401

        else:

            # Decode the payload (add padding if needed)

            payload = parts[1]

            padding = 4 - len(payload) % 4

            if padding != 4:

                payload += '=' * padding

            

            decoded = base64.urlsafe_b64decode(payload)

            idinfo = json.loads(decoded)

            

            print(f"[GOOGLE_AUTH] Decoded token - email: {idinfo.get('email')}, aud: {idinfo.get('aud')}, azp: {idinfo.get('azp')}")

            

            # For now, trust the token if it has required fields

            if not idinfo.get('email') or not idinfo.get('sub'):

                print(f"[GOOGLE_AUTH] Token missing required fields")

                return jsonify({"error": "Invalid token - missing fields"}), 401



        # ID token is valid. Get the user's Google ID (sub), email, and name.
        email = idinfo['email']

        name = idinfo.get('name', 'Google User')

        google_id = idinfo['sub']

        google_email_verified = idinfo.get('email_verified', False)

        # Use a fresh direct connection to avoid g.db_conn aborted-transaction cascade
        import psycopg as _psycopg_ga
        from config import SUPABASE_DB_URL as _GA_DB_URL
        from psycopg.rows import dict_row as _dict_row_ga

        _ga_conn = _psycopg_ga.connect(conninfo=_GA_DB_URL, row_factory=_dict_row_ga)
        try:
            with _ga_conn.cursor() as _gc:
                # 1. Find the user
                _gc.execute("SELECT id, full_name, email FROM users WHERE email = %s", (email,))
                user = _gc.fetchone()

                if user:
                    # 2a. User exists — try to update google_id / auth_provider / force_logout_at
                    try:
                        _gc.execute(
                            "UPDATE users SET google_id = %s, auth_provider = 'google', force_logout_at = NULL WHERE email = %s",
                            (google_id, email)
                        )
                        _ga_conn.commit()
                        print(f"[GOOGLE_AUTH] Updated existing user google_id for {email}")
                    except Exception as _ue:
                        _ga_conn.rollback()
                        print(f"[GOOGLE_AUTH] UPDATE google_id failed (non-fatal): {_ue}")

                    # 3. Re-fetch fresh user data
                    try:
                        _gc.execute(
                            "SELECT id, full_name, is_email_verified, is_driver, is_verified, loyalty_points FROM users WHERE email = %s",
                            (email,)
                        )
                        user_fresh = _gc.fetchone() or {}
                    except Exception as _rfe:
                        _ga_conn.rollback()
                        print(f"[GOOGLE_AUTH] Re-fetch failed: {_rfe}")
                        # Fallback: use what we know
                        user_fresh = {'id': user['id'], 'full_name': user['full_name']}

                    user_id    = user_fresh.get('id') or user['id']
                    full_name  = user_fresh.get('full_name') or user['full_name']
                    is_drv     = int(user_fresh.get('is_driver') or 0)
                    is_ver     = int(user_fresh.get('is_verified') or 0)
                    lp         = int(user_fresh.get('loyalty_points') or 0)
                    email_ver  = bool(user_fresh.get('is_email_verified') or google_email_verified)

                    # 4. If Google says email is verified, mark it in DB
                    if google_email_verified and not user_fresh.get('is_email_verified'):
                        try:
                            _gc.execute("UPDATE users SET is_email_verified = TRUE WHERE email = %s", (email,))
                            _ga_conn.commit()
                        except Exception as _eve:
                            _ga_conn.rollback()
                            print(f"[GOOGLE_AUTH] Mark email_verified failed (non-fatal): {_eve}")

                    # Google emails are always verified — skip OTP
                    return jsonify({
                        "message": "login success",
                        "user": {
                            "id": user_id,
                            "fullName": full_name,
                            "email": email,
                            "isDriver": is_drv,
                            "isVerified": is_ver,
                            "loyaltyPoints": lp
                        },
                        "verification_required": False
                    }), 200

                else:
                    # 2b. New user — insert (split Google name into first/last)
                    _name_parts = (name or '').strip().split(' ', 1)
                    _first = _name_parts[0] if _name_parts else name
                    _last = _name_parts[1] if len(_name_parts) > 1 else ''
                    try:
                        _gc.execute(
                            "INSERT INTO users (first_name, last_name, email, google_id, auth_provider, is_driver, is_email_verified, is_verified) VALUES (%s, %s, %s, %s, 'google', %s, %s, 0) RETURNING id",
                            (_first, _last, email, google_id, is_driver, google_email_verified)
                        )
                        new_row = _gc.fetchone()
                        new_user_id = new_row['id'] if new_row else None
                        _ga_conn.commit()
                    except Exception as _ie:
                        _ga_conn.rollback()
                        # Insert might fail if google_id/auth_provider columns don't exist yet
                        print(f"[GOOGLE_AUTH] INSERT with google columns failed: {_ie}, trying basic insert")
                        _gc.execute(
                            "INSERT INTO users (first_name, last_name, email, is_driver, is_email_verified, is_verified) VALUES (%s, %s, %s, %s, %s, 0) RETURNING id",
                            (_first, _last, email, is_driver, google_email_verified)
                        )
                        new_row = _gc.fetchone()
                        new_user_id = new_row['id'] if new_row else None
                        _ga_conn.commit()

                    return jsonify({
                        "message": "login success",
                        "user": {
                            "id": new_user_id,
                            "fullName": name,
                            "email": email,
                            "isDriver": is_driver,
                            "isVerified": 0,
                            "loyaltyPoints": 0
                        },
                        "verification_required": False
                    }), 201

        finally:
            _ga_conn.close()



    except ValueError:

        # Invalid token

        return jsonify({"error": "Invalid Google token"}), 401

    except Exception as e:

        return jsonify({"error": str(e)}), 500




@app.route('/users/<int:user_id>/fcm-token', methods=['POST'])
def register_fcm_token(user_id):
    """Register or update FCM token for push notifications"""
    try:
        data = request.get_json() or {}
        fcm_token = data.get('fcm_token', '').strip()
        
        if not fcm_token:
            return jsonify({"error": "fcm_token is required"}), 400
            
        cur = get_cursor()
        
        # Update user's FCM token
        cur.execute(
            "UPDATE users SET fcm_token = %s WHERE id = %s",
            (fcm_token, user_id)
        )
        
        commit_db()
        
        return jsonify({
            "message": "FCM token registered successfully",
            "user_id": user_id
        }), 200
        
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/test-fcm-config', methods=['GET'])
def test_fcm_config():
    """Test FCM configuration and show detailed status"""
    try:
        from config import FCM_SERVER_KEY
        import os
        
        # Check configuration
        server_key = os.environ.get('FCM_SERVER_KEY', FCM_SERVER_KEY)
        
        config_status = {
            'fcm_server_key_configured': bool(server_key and server_key.strip() != ''),
            'fcm_server_key_length': len(server_key) if server_key else 0,
            'fcm_server_key_preview': f"{server_key[:10]}...{server_key[-10:]}" if server_key and len(server_key) > 20 else server_key,
            'environment_fcm_key': bool(os.environ.get('FCM_SERVER_KEY')),
        }
        
        # Test FCM service
        try:
            from notifications import fcm_service
            # Try to get access token (V1 API test)
            try:
                access_token = fcm_service._get_access_token()
                config_status['fcm_v1_api_token'] = bool(access_token)
            except Exception as v1_err:
                config_status['fcm_v1_api_error'] = str(v1_err)
                config_status['fcm_v1_api_token'] = False
        except Exception as fcm_err:
            config_status['fcm_service_error'] = str(fcm_err)
        
        return jsonify({
            'status': 'success',
            'config': config_status,
            'message': 'FCM configuration test completed'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/test-push/<int:user_id>', methods=['POST'])
def test_push_notification(user_id):
    """Test endpoint to send push notification to a user"""
    try:
        data = request.get_json() or {}
        title = data.get('title', 'Test Notification')
        message = data.get('message', 'This is a test push notification from Autoride')
        
        # Send both in-app and push notification
        from notifications import notification_service
        success = notification_service.notify_user(
            user_id,
            title,
            message,
            'test_notification'
        )
        
        if success:
            return jsonify({
                "message": "Test notification sent successfully",
                "user_id": user_id
            }), 200
        else:
            return jsonify({"error": "Failed to send notification"}), 500
            
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/admin/send-custom-push', methods=['POST'])
def admin_send_custom_push():
    """Admin endpoint to send custom push notification or broadcast to all users"""
    try:
        data = request.get_json() or {}
        title = data.get('title', '').strip()
        body = data.get('body', '').strip()
        user_id = data.get('user_id')
        broadcast = data.get('broadcast', False)
        
        if not title or not body:
            return jsonify({"error": "Title and body are required"}), 400
            
        from notifications import notification_service
        
        if broadcast:
            # Send to all users using the existing database cursor/transaction
            cur = get_cursor()
            cur.execute("SELECT id, fcm_token FROM users")
            users = cur.fetchall()
            
            success_count = 0
            # 1. Bulk insert in-app notifications
            for u in users:
                try:
                    cur.execute(
                        """
                        INSERT INTO notifications (user_id, admin_id, title, message, type)
                        VALUES (%s, NULL, %s, %s, %s)
                        """,
                        (u['id'], title, body, 'admin_broadcast')
                    )
                    success_count += 1
                except Exception as e:
                    print(f"Failed to insert in-app notification for user {u['id']}: {e}")
            
            # Commit the changes to the database
            commit_db()
            
            # 2. Dispatch FCM push notifications for users who have tokens
            try:
                from notifications import fcm_service
                for u in users:
                    token = u.get('fcm_token')
                    if token:
                        try:
                            fcm_service.send_push(token, title, body, channel_id='autoride_customer_high_priority')
                        except Exception as push_err:
                            print(f"FCM push failed for user {u['id']}: {push_err}")
            except Exception as fcm_err:
                print(f"FCM service error: {fcm_err}")
                
            return jsonify({
                "message": f"Broadcast push notification sent successfully to {success_count} users."
            }), 200
        else:
            if not user_id:
                return jsonify({"error": "User ID is required for sending individual notification"}), 400
                
            ok = notification_service.notify_user(
                int(user_id),
                title,
                body,
                'admin_custom_push'
            )
            if ok:
                return jsonify({"message": "Push notification sent successfully"}), 200
            else:
                return jsonify({"error": "Failed to send notification. User might not have a registered device/token."}), 500
                
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500



@app.route('/admin/upload-refund-proof', methods=['POST'])

def upload_refund_proof():

    booking_id = request.form.get('booking_id')

    admin_id = request.form.get('admin_id')

    

    if not booking_id or not admin_id:

        return jsonify({"error": "Booking ID and Admin ID are required"}), 400



    if 'proof' not in request.files:

        return jsonify({"error": "No proof file uploaded"}), 400

        

    file = request.files['proof']

    if file.filename == '':

        return jsonify({"error": "No selected file"}), 400

        

    try:

        cur = get_cursor()

        

        # Ensure column exists

        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_proof_url TEXT")

        

        filename = secure_filename(f"refund_{booking_id}_{int(datetime.now().timestamp())}_{file.filename}")

        # Read file bytes
        file_bytes = file.read()
        url = None  # Will only be set if Supabase upload succeeds

        # Upload to Supabase Storage for persistent public access
        try:
            import urllib.request as _urlreq
            import urllib.error as _urlerr
            import json as _json
            from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
            _auth_headers = {
                'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
                'apikey': SUPABASE_SERVICE_KEY
            }
            # Ensure bucket exists (public)
            _bucket_data = _json.dumps({'id': 'refund-proofs', 'name': 'refund-proofs', 'public': True}).encode()
            _bucket_req = _urlreq.Request(
                f"{SUPABASE_URL}/storage/v1/bucket",
                data=_bucket_data,
                headers={**_auth_headers, 'Content-Type': 'application/json'},
                method='POST'
            )
            try: _urlreq.urlopen(_bucket_req, timeout=5)
            except Exception: pass
            # Upload file
            supa_path = f"refund-proofs/{filename}"
            _upload_req = _urlreq.Request(
                f"{SUPABASE_URL}/storage/v1/object/{supa_path}",
                data=file_bytes,
                headers={**_auth_headers, 'Content-Type': file.content_type or 'image/jpeg', 'x-upsert': 'true'},
                method='POST'
            )
            with _urlreq.urlopen(_upload_req, timeout=15) as _resp:
                if _resp.status in (200, 201):
                    url = f"{SUPABASE_URL}/storage/v1/object/public/refund-proofs/{filename}"
        except Exception as _supa_err:
            print(f"Supabase upload failed: {_supa_err}")
            return jsonify({"error": "Failed to upload proof image. Please check your internet connection and try again."}), 500

        if not url:
            return jsonify({"error": "Failed to upload proof image to storage. Please try again."}), 500

        ref_val = request.form.get('refund_ref', '').strip()
        cur.execute("""

            UPDATE bookings 

            SET payment_status = 'Refunded', 

                refund_proof_url = %s,
                refunded_at = NOW(),
                refund_ref = CASE WHEN %s != '' THEN %s ELSE refund_ref END

            WHERE id = %s

        """, (url, ref_val, ref_val, booking_id))
        commit_db()  # Commit immediately after the status update

        # Notify customer
        try:
            cur2 = get_cursor()
            cur2.execute('SELECT user_id, refund_amount FROM bookings WHERE id = %s', (booking_id,))
            bk = cur2.fetchone()
            if bk and bk['user_id']:
                notification_service.notify_user(
                    bk['user_id'],
                    'Refund Processed',
                    f"Your refund of PHP {float(bk['refund_amount'] or 0):,.2f} for Booking #{booking_id} has been sent. Please check your account.",
                    'refund_processed'
                )
            cur2.close()
        except Exception:
            pass

        # Log activity (skip if admin_id not in admins table)
        try:
            cur.execute("SELECT username FROM admins WHERE id = %s", (admin_id,))

            admin = cur.fetchone()

            admin_name = admin['username'] if admin else f"Admin {admin_id}"

            if admin:
                log_activity(admin_id, admin_name, "Uploaded refund proof", "booking", booking_id, f"Marked as Refunded. Receipt: {url}")
        except Exception:
            pass

        

        commit_db()

        return jsonify({"message": "Refund proof uploaded and booking updated to Refunded.", "url": url}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



# Legacy vehicle routes removed to resolve duplicate endpoint conflicts.


@app.route('/admin/process-refund', methods=['POST'])
def process_refund():
    """
    Record a manual refund (cash / GCash send-money / etc.) and notify the customer.
    Accepts JSON or multipart (for optional proof screenshot upload).
    """
    import datetime as _dtmod

    ct = request.content_type or ''
    if 'multipart/form-data' in ct or 'application/x-www-form-urlencoded' in ct:
        form = request.form
        booking_id     = form.get('booking_id')
        extension_id   = form.get('extension_id')   # optional - for extension refunds
        admin_id       = form.get('admin_id')
        refund_amount  = form.get('refund_amount')
        refund_method  = form.get('refund_method', 'GCash')
        refund_ref     = form.get('refund_ref', '')
        refund_note    = form.get('refund_note', '')
    else:
        data = request.get_json(silent=True) or {}
        booking_id     = data.get('booking_id')
        extension_id   = data.get('extension_id')
        admin_id       = data.get('admin_id')
        refund_amount  = data.get('refund_amount')
        refund_method  = data.get('refund_method', 'GCash')
        refund_ref     = data.get('refund_ref', '')
        refund_note    = data.get('refund_note', '')

    if not booking_id or not admin_id or not refund_amount:
        return jsonify({"error": "booking_id, admin_id, and refund_amount are required"}), 400

    try:
        cur = get_cursor()

        # Ensure columns exist
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_proof_url TEXT")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_amount NUMERIC(12,2)")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_method VARCHAR(100)")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_ref VARCHAR(200)")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_note TEXT")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMPTZ")
        commit_db()

        # Handle optional proof screenshot
        proof_url = None
        if 'proof' in request.files:
            from werkzeug.utils import secure_filename as _sf
            f = request.files['proof']
            if f and f.filename:
                fname = _sf(f"refund_{booking_id}_{int(_dtmod.datetime.now().timestamp())}_{f.filename}")
                fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
                f.save(fpath)
                proof_url = f"/uploads/{fname}"

        # If this is an extension refund, mark the extension row
        if extension_id:
            cur.execute(
                "UPDATE booking_extensions SET admin_note = COALESCE(admin_note,'') || ' | Refunded: ' || %s WHERE id = %s",
                (f"PHP {refund_amount} via {refund_method} ref#{refund_ref}", extension_id)
            )

        # Update booking - mark payment_status as Refunded
        cur.execute("""
            UPDATE bookings
            SET payment_status   = 'Refunded',
                refund_amount    = %s,
                refund_method    = %s,
                refund_ref       = %s,
                refund_note      = %s,
                refund_proof_url = COALESCE(%s, refund_proof_url),
                refunded_at      = NOW()
            WHERE id = %s
        """, (float(refund_amount), refund_method, refund_ref or None,
              refund_note or None, proof_url, booking_id))

        # Get customer user_id for notification
        cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))
        bk = cur.fetchone()

        # Log activity
        cur.execute("SELECT username FROM admins WHERE id = %s", (admin_id,))
        adm = cur.fetchone()
        admin_name = adm['username'] if adm else f"Admin {admin_id}"
        log_activity(admin_id, admin_name, "Processed refund", "booking", booking_id,
                     f"PHP {refund_amount} via {refund_method}. Ref: {refund_ref}")

        commit_db()

        # Notify customer
        if bk:
            try:
                from notifications import notification_service
                ref_display = f" (Ref: {refund_ref})" if refund_ref else ""
                notification_service.notify_user(
                    bk['user_id'],
                    "Refund Processed",
                    f"Your refund of PHP {float(refund_amount):,.2f} has been sent via {refund_method}{ref_display}. Booking #{booking_id}.",
                    'refund_processed'
                )
            except Exception:
                pass

        return jsonify({
            "message": f"Refund of PHP {float(refund_amount):,.2f} recorded successfully.",
            "booking_id": booking_id,
            "refund_amount": float(refund_amount),
            "refund_method": refund_method
        }), 200

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()



# --- GPS TRACKING ROUTES ---

@app.route('/vehicles/<int:vehicle_id>/location', methods=['POST'])

def update_vehicle_location(vehicle_id):

    """Update GPS coordinates for a specific vehicle."""

    data = request.json

    lat = data.get('latitude')

    lng = data.get('longitude')

    

    if lat is None or lng is None:

        return jsonify({"error": "Latitude and Longitude are required"}), 400

        

    try:

        cur = get_cursor()

        cur.execute("""

            UPDATE vehicles 

            SET latitude = %s, longitude = %s, last_gps_update = CURRENT_TIMESTAMP 

            WHERE id = %s

        """, (lat, lng, vehicle_id))

        commit_db()

        return jsonify({"message": "Location updated successfully"}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/admin/gps-locations', methods=['GET'])

def get_all_gps_locations():

    """Fetch real-time location for all active vehicles."""

    admin_id = request.args.get('admin_id')

    try:

        cur = get_cursor()

        

        # Determine location filter

        location_filter = None

        if admin_id:

            cur.execute("SELECT role, assigned_location FROM users WHERE id = %s", (admin_id,))

            adm = cur.fetchone()

            if adm and adm['role'] == 'admin' and adm['assigned_location']:

                location_filter = adm['assigned_location']



        query = """

            SELECT id, name, plate_number, latitude, longitude, last_gps_update, status

            FROM vehicles 

            WHERE latitude IS NOT NULL AND longitude IS NOT NULL

        """

        params = []

        if location_filter:

            query += " AND location = %s "

            params.append(location_filter)

            

        cur.execute(query, tuple(params))

        locations = cur.fetchall()

        return jsonify([dict(loc) for loc in locations]), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/vehicle/<int:vehicle_id>', methods=['GET'])

def get_vehicle(vehicle_id):

    user_id = request.args.get('user_id')

    try:

        cur = get_cursor()

        # Fetch vehicle details

        cur.execute("SELECT * FROM vehicles WHERE id = %s", (vehicle_id,))

        vehicle = cur.fetchone()

        

        if vehicle:

            vehicle_dict: typing.Dict[str, typing.Any] = dict(vehicle)

            

            # Fetch reviews

            cur.execute("""

                SELECT r.*, u.full_name, u.profile_picture 

                FROM reviews r

                JOIN users u ON r.user_id = u.id

                WHERE r.vehicle_id = %s

                ORDER BY r.created_at DESC

            """, (vehicle_id,))

            reviews = cur.fetchall()

            vehicle_dict['reviews'] = [dict(r) for r in reviews]

            

            # Avg Rating

            cur.execute("SELECT AVG(rating) as avg_rating FROM reviews WHERE vehicle_id = %s", (vehicle_id,))

            avg_row = cur.fetchone()

            avg = avg_row['avg_rating'] if avg_row else None

            vehicle_dict['avg_rating'] = float(avg) if avg else 0

            

            # Favorite status

            vehicle_dict['is_favorite'] = False

            if user_id and user_id != 'null':

                cur.execute("SELECT * FROM favorites WHERE user_id = %s AND vehicle_id = %s", (user_id, vehicle_id))

                if cur.fetchone():

                    vehicle_dict['is_favorite'] = True

            

            # Fetch Gallery Images

            try:

                cur.execute("SELECT id, image_path, is_primary, order_index FROM vehicle_images WHERE vehicle_id = %s ORDER BY order_index ASC, id ASC", (vehicle_id,))

                gallery_images = cur.fetchall()

            except Exception:

                cur.execute("SELECT id, image_path, is_primary, id as order_index FROM vehicle_images WHERE vehicle_id = %s ORDER BY id ASC", (vehicle_id,))

                gallery_images = cur.fetchall()



            vehicle_dict['gallery'] = [row['image_path'] for row in gallery_images]

            vehicle_dict['gallery_details'] = [dict(row) for row in gallery_images]



            # Fetch globally active Pickup Instructions

            cur.execute("SELECT description FROM pickup_instructions")

            instructions = cur.fetchall()

            vehicle_dict['pickup_instructions'] = [row['description'] for row in instructions]

                    

            return jsonify(vehicle_dict), 200

        else:

            return jsonify({"error": "Vehicle not found"}), 404

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/vehicles/images/<int:image_id>', methods=['DELETE'])

def delete_vehicle_image(image_id):


    try:

        cur = get_cursor()

        # Get path to delete from Supabase if needed (optional for now as we just clear from DB)

        cur.execute("SELECT image_path, vehicle_id FROM vehicle_images WHERE id = %s", (image_id,))

        img = cur.fetchone()

        if not img:

            return jsonify({"error": "Image not found"}), 404

        

        path = img['image_path']

        v_id = img['vehicle_id']

        

        # Delete from DB

        cur.execute("DELETE FROM vehicle_images WHERE id = %s", (image_id,))

        

        # Check if we need to update the main vehicle image

        cur.execute("SELECT vehicle_image, name FROM vehicles WHERE id = %s", (v_id,))

        v_row = cur.fetchone()

        if v_row and v_row['vehicle_image'] == path:

            # Pick another image as primary if exists

            try:

                cur.execute("SELECT image_path FROM vehicle_images WHERE vehicle_id = %s ORDER BY order_index ASC, id ASC LIMIT 1", (v_id,))

                next_img = cur.fetchone()

            except Exception:

                cur.execute("SELECT image_path FROM vehicle_images WHERE vehicle_id = %s ORDER BY id ASC LIMIT 1", (v_id,))

                next_img = cur.fetchone()

            

            new_path = next_img['image_path'] if next_img else ''

            cur.execute("UPDATE vehicles SET vehicle_image = %s WHERE id = %s", (new_path, v_id))



        commit_db()



        # Log activity

        log_activity(

            admin_id=0, 

            admin_name='System/Admin', 

            action='DELETE_VEHICLE_IMAGE',

            target_type='VEHICLE',

            target_id=str(v_id),

            details=f"Deleted an image from vehicle: {v_row['name'] if v_row else v_id}"

        )



        return jsonify({"message": "Image deleted"}), 200

    except Exception as e:

        print(f"DELETE IMAGE ERROR: {e}")

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/vehicles/<int:vehicle_id>/images/order', methods=['PUT'])

def update_image_order(vehicle_id):

    data = request.json

    order = data.get('order') # Expecting list of image IDs in order

    if not order:

        return jsonify({"error": "Order list is required"}), 400

    

    try:

        cur = get_cursor()

        for index, img_id in enumerate(order):

            try:

                cur.execute("UPDATE vehicle_images SET order_index = %s WHERE id = %s AND vehicle_id = %s", (index, img_id, vehicle_id))

            except Exception:

                # Can't update order if column missing

                pass

        

        # Update primary image to be the first in order

        cur.execute("SELECT image_path FROM vehicle_images WHERE vehicle_id = %s ORDER BY order_index ASC, id ASC LIMIT 1", (vehicle_id,))

        first = cur.fetchone()

        if first:

            cur.execute("UPDATE vehicles SET vehicle_image = %s WHERE id = %s", (first['image_path'], vehicle_id))

            

        commit_db()

        return jsonify({"message": "Order updated"}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/maintenance/migrate', methods=['GET'])

def run_migration():

    try:

        cur = get_cursor()

        cur.execute("ALTER TABLE vehicle_images ADD COLUMN IF NOT EXISTS order_index INTEGER DEFAULT 0;")

        commit_db()

        return jsonify({"message": "Migration successful"}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/book', methods=['POST'])

def book():

    data = request.json

    try:

        user_id = data.get('user_id')

        vehicle_id = data.get('vehicle_id')

        start_date = data.get('start_date')

        end_date = data.get('end_date')

        pickup_location = data.get('pickup_location')

        rental_type = data.get('rental_type')

        

        cur = get_cursor()



        # Security Check: Driver's License Verification (Must be 2 = Verified)

        cur.execute("SELECT is_verified FROM users WHERE id = %s", (user_id,))

        user_status = cur.fetchone()

        if not user_status or user_status['is_verified'] != 2:

            msg = "Your driver's license must be APPROVED by an admin before you can book." if user_status and user_status['is_verified'] == 1 else "Please upload your driver's license to proceed."

            return jsonify({

                "error": "Account not verified.", 

                "message": msg,

                "is_verified": user_status['is_verified'] if user_status else 0

            }), 403

        # 1 booking per account - reject if user already has an active booking

        cur.execute("""
            SELECT id, status FROM bookings
            WHERE user_id = %s
              AND status IN ('Pending', 'Confirmed', 'Approved', 'Picked Up', 'Ongoing')
            LIMIT 1
        """, (user_id,))

        existing = cur.fetchone()

        if existing:

            return jsonify({
                "error": "You already have an active booking (#{id}, status: {status}). "
                         "Please complete or cancel it before making a new booking.".format(
                             id=existing['id'], status=existing['status'])
            }), 409



        # ── Overlap guard: reject if the requested vehicle_id already has an active booking that overlaps ──
        cur.execute("""
            SELECT id, start_date, end_date, status,
                   (end_date + INTERVAL '1 day')::date AS next_available
            FROM bookings
            WHERE vehicle_id = %s
              AND status IN ('Pending', 'Confirmed', 'Approved', 'Picked Up', 'Ongoing')
              AND start_date <= %s
              AND end_date >= %s
            ORDER BY start_date ASC
            LIMIT 1
        """, (vehicle_id, end_date, start_date))

        overlap = cur.fetchone()
        if overlap:
            o = dict(overlap)
            return jsonify({
                "error": "This vehicle is already booked from {start} to {end} (status: {status}). "
                         "It will be available again from {next}.".format(
                             start=str(o['start_date']), end=str(o['end_date']),
                             status=o['status'], next=str(o['next_available']))
            }), 409

        # Category Auto-Assignment Logic

        # Get category info from the representative vehicle_id

        cur.execute("SELECT brand, model FROM vehicles WHERE id = %s", (vehicle_id,))

        category = cur.fetchone()

        if not category:

            return jsonify({"error": "Invalid vehicle category."}), 404

            

        # Find first available unit in this category for the given dates

        cur.execute("""

            SELECT id FROM vehicles 

            WHERE brand = %s AND model = %s 

            AND status NOT IN ('Maintenance', 'Repair', 'Service', 'Sold')

            AND id NOT IN (

                SELECT vehicle_id FROM bookings 

                WHERE status IN ('Pending', 'Confirmed', 'Approved', 'Picked Up', 'Ongoing')

                AND (start_date <= %s AND end_date >= %s)

            )

            LIMIT 1

        """, (category['brand'], category['model'], end_date, start_date))

        

        available_unit = cur.fetchone()

        if not available_unit:

            return jsonify({"error": "No units available for this model on the selected dates."}), 400

            

        # Use the actual available unit ID for the booking

        final_vehicle_id = available_unit['id']



        # Granular locations

        pickup_province = data.get('pickup_province')

        pickup_municipality = data.get('pickup_municipality')

        pickup_barangay = data.get('pickup_barangay')

        return_province = data.get('return_province')

        return_municipality = data.get('return_municipality')

        return_barangay = data.get('return_barangay')

        pickup_time = data.get('pickup_time', '06:00')

        return_time = data.get('return_time', '06:00')

        service_type = data.get('service_type', 'pickup')



        # New fields
        addons = ",".join(data.get('addons', []))
        base_price = data.get('base_price')
        addon_price = data.get('addon_price')
        tax_amount = data.get('tax_amount')
        total_price = data.get('total_price')

        points_redeemed = int(data.get('points_redeemed', 0) or 0)
        points_earned = int(data.get('points_earned', 0) or 0)
        delivery_fee = float(data.get('delivery_fee', 0.00) or 0.00)

        # Validate points
        if points_redeemed > 0:
            cur.execute("SELECT loyalty_points FROM users WHERE id = %s", (user_id,))
            user_pts = cur.fetchone()
            if not user_pts or int(user_pts['loyalty_points'] or 0) < points_redeemed:
                return jsonify({"error": "Insufficient loyalty points"}), 400

        cur.execute("""
            INSERT INTO bookings (
                user_id, vehicle_id, start_date, end_date, pickup_location, rental_type, addons, 
                base_price, addon_price, tax_amount, total_price, status,
                pickup_province, pickup_municipality, pickup_barangay,
                return_province, return_municipality, return_barangay,
                start_time, end_time, service_type, delivery_fee, points_redeemed, points_earned
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (user_id, final_vehicle_id, start_date, end_date, pickup_location, rental_type, addons, 
              base_price, addon_price, tax_amount, total_price,
              pickup_province, pickup_municipality, pickup_barangay,
              return_province, return_municipality, return_barangay,
              pickup_time, return_time, service_type, delivery_fee, points_redeemed, points_earned))

        booking_id = cur.fetchone()['id']

        # Deduct loyalty points immediately
        if points_redeemed > 0:
            cur.execute("UPDATE users SET loyalty_points = loyalty_points - %s WHERE id = %s", (points_redeemed, user_id))

        


        

        # Update vehicle status to 'Booked'

        cur.execute("UPDATE vehicles SET status = 'Booked' WHERE id = %s", (final_vehicle_id,))


        

        commit_db()

        return jsonify({"message": "Booking created", "booking_id": booking_id}), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/legacy-payment', methods=['POST'])

def legacy_payment():

    try:

        booking_id = request.form.get('booking_id')

        amount = request.form.get('amount')

        method = request.form.get('method')

        reference_number = request.form.get('reference_number', '')

        

        cur = get_cursor()

        

        # Security Check: Verification Status

        cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))

        booking_row = cur.fetchone()

        if booking_row:

            cur.execute("SELECT is_verified FROM users WHERE id = %s", (booking_row['user_id'],))

            user_status = cur.fetchone()

            if not user_status or user_status['is_verified'] != 2:

                return jsonify({

                    "error": "Account not verified", 

                    "message": "Your account must be fully verified by an admin before completing payment."

                }), 403

        

        filepath = ""

        if 'payment_proof' in request.files:

            file = request.files['payment_proof']

            if file and file.filename:

                filename = secure_filename(file.filename)

                if filename:

                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                    file.save(filepath)

                    # Store relative path for db

                    filepath = filename



        cur = get_cursor()

        cur.execute("""

            INSERT INTO payments(booking_id, amount, method, reference_number, payment_proof, status)

            VALUES(%s, %s, %s, %s, %s, %s)

        """, (booking_id, amount, method, reference_number, filepath, 'Completed'))

        

        # Also update booking status

        cur.execute("UPDATE bookings SET status='Confirmed' WHERE id=%s", (booking_id,))

        


        

        # Ensure vehicle status is 'Booked'

        cur.execute("UPDATE vehicles SET status='Booked' WHERE id=(SELECT vehicle_id FROM bookings WHERE id=%s)", (booking_id,))


        

        # Get details for receipt email
        cur.execute("""
            SELECT b.id, u.email, u.full_name, v.brand, v.model,
                   b.start_date, b.end_date, b.total_price, b.amount_paid,
                   b.addons, b.insurance_type, b.insurance_price,
                   b.base_price, b.addon_price, b.discount_amount,
                   b.payment_type, b.balance_amount,
                   p.reference_number, p.method
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN vehicles v ON b.vehicle_id = v.id
            JOIN payments p ON p.booking_id = b.id
            WHERE b.id = %s
            ORDER BY p.id DESC LIMIT 1
        """, (booking_id,))

        details = cur.fetchone()

        

        if details:

            details_dict = dict(details)

            send_receipt_email(details['email'], details_dict)

            

            commit_db()

            # Send in-app notifications after successful commit
            try:
                user_id_sms = details_dict.get('user_id') or (booking_row['user_id'] if booking_row else None)
                if not user_id_sms:
                    cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))
                    bk_row = cur.fetchone()
                    user_id_sms = bk_row['user_id'] if bk_row else None
                if user_id_sms:
                    notification_service.notify_user(
                        user_id_sms,
                        "Payment Confirmed",
                        f"Payment proof received for booking #{booking_id}. Amount: PHP {float(amount or 0)}.",
                        'payment_confirmed'
                    )
                customer_name = details_dict.get('full_name', 'Customer')
                notification_service.notify_admins_inapp(
                    "Payment Proof Uploaded",
                    f"Payment proof uploaded for booking #{booking_id} by {customer_name}. Amount: PHP {float(amount or 0)}.",
                    'admin_payment_proof',
                    type='admin_payment_proof',
                    booking_id=booking_id
                )
            except Exception as notif_err:
                print(f"ERROR SENDING PAYMENT NOTIFICATION: {notif_err}")

            return jsonify({

                "message": "Payment successful",

                "receipt": {

                    "id": details_dict['id'],

                    "amount": float(details_dict['total_price']),

                    "brand": details_dict['brand'],

                    "model": details_dict['model'],

                    "start_date": str(details_dict['start_date']),

                    "end_date": str(details_dict['end_date']),

                    "reference_number": details_dict['reference_number'],

                    "method": details_dict['method'],

                    "date": datetime.now().strftime("%Y-%m-%d"),

                    "time": datetime.now().strftime("%I:%M %p")

                }

            }), 201

        

        commit_db()
        # Send in-app notification after successful commit
        try:
            user_id_sms = details_dict.get('user_id') or (booking_row['user_id'] if booking_row else None)
            if not user_id_sms:
                cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))
                bk_row = cur.fetchone()
                user_id_sms = bk_row['user_id'] if bk_row else None
            if user_id_sms:
                notification_service.notify_user(
                    user_id_sms,
                    "Payment Confirmed",
                    f"Payment proof received for booking #{booking_id}. Amount: PHP {float(amount or 0)}.",
                    'payment_confirmed'
                )
            customer_name = details_dict.get('full_name', 'Customer')
            notification_service.notify_admins_inapp(
                "Payment Proof Uploaded",
                f"Payment proof uploaded for booking #{booking_id} by {customer_name}. Amount: PHP {float(amount or 0)}.",
                'admin_payment_proof',
                type='payment',
                booking_id=booking_id
            )
        except Exception as notif_err:
            print(f"ERROR SENDING PAYMENT NOTIFICATION: {notif_err}")
        return jsonify({"message": "Payment successful"}), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/user-bookings', methods=['GET'])

def user_bookings():

    user_id = request.args.get('user_id')

    if not user_id:

        return jsonify({"error": "user_id is required"}), 400

        

    try:

        try:
            from routers.paymongo_routes import check_and_update_unpaid_paymongo_bookings
            check_and_update_unpaid_paymongo_bookings(user_id)
        except Exception as pm_err:
            print(f"Auto status check error: {pm_err}")

        cur = get_cursor()

        # Fetch bookings with vehicle info and license/emergency contact details
        query = """
            SELECT b.id, b.user_id, b.vehicle_id, b.start_date, b.end_date,
                   b.pickup_location, b.rental_type, b.addons, b.insurance_type, b.insurance_price,
                   b.base_price, b.addon_price, b.total_price, b.status, b.payment_status,
                   b.payment_type, b.amount_paid, b.balance_amount,
                   b.applied_coupon_id, b.discount_amount, b.points_redeemed, b.points_earned,
                   b.cancellation_reason, b.cancelled_by,
                   COALESCE(b.refund_amount, 0) AS refund_amount,
                   b.refund_method, b.refund_ref, b.refund_note,
                   b.refund_channel, b.refund_account_name, b.refund_account_number,
                   CAST(b.refunded_at AS TEXT) AS refunded_at,
                   b.refund_proof_url,
                   b.is_conflict_affected,
                   b.conflict_id,
                   v.brand, v.model, v.plate_number, v.vehicle_image, v.daily_rate, v.color,
                   COALESCE(ld.full_name, u.full_name) AS license_full_name,
                   COALESCE(ld.license_number, u.license_number) AS license_number,
                   COALESCE(CAST(ld.expiry_date AS TEXT), CAST(u.license_expiry AS TEXT)) AS license_expiry,
                   CAST(ld.date_of_birth AS TEXT) AS date_of_birth,
                   ld.license_front_url, ld.license_back_url,
                   ld.emergency_contact_name, ld.emergency_contact_phone,
                   ld.emergency_contact_relationship
            FROM bookings b
            LEFT JOIN vehicles v ON b.vehicle_id = v.id
            LEFT JOIN users u ON b.user_id = u.id
            LEFT JOIN license_details ld ON b.user_id = ld.user_id
            WHERE b.user_id = %s
            ORDER BY b.id DESC
        """

        cur.execute(query, (user_id,))

        data = cur.fetchall()

        bookings_list = [dict(row) for row in data]

        return jsonify(bookings_list), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/profile', methods=['GET'])

def profile():

    user_id = request.args.get('user_id')

    if not user_id:

        return jsonify({"error": "user_id is required"}), 400

        

    try:

        cur = get_cursor()

        cur.execute("SELECT id, full_name, email, phone, license_image, profile_picture, is_verified FROM users WHERE id=%s", (user_id,))

        user = cur.fetchone()

        

        if user:

            return jsonify(dict(user)), 200

        else:

            return jsonify({"error": "User not found"}), 404

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/user/change-password', methods=['POST'])
def user_change_password():
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not user_id or not new_password:
            return jsonify({'error': 'Missing required fields.'}), 400

        cur = get_cursor()
        cur.execute("SELECT id, password FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if not user:
            cur.close()
            return jsonify({'error': 'User not found.'}), 404

        stored_password = user['password'] or ''

        # If they already have a password set, require them to provide the correct current password
        if stored_password:
            if not current_password:
                cur.close()
                return jsonify({'error': 'Current password is required to change password.'}), 400
            
            pw_ok = False
            try:
                pw_ok = bcrypt.checkpw(current_password.encode('utf-8'), stored_password.encode('utf-8'))
            except:
                pw_ok = (stored_password == current_password)
            
            if not pw_ok:
                cur.close()
                return jsonify({'error': 'Incorrect current password.'}), 400

        hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_pw, user_id))
        cur.close()

        return jsonify({'message': 'Password updated successfully!'}), 200
    except Exception as e:
        print(f"Error updating password: {e}")
        return jsonify({'error': 'Internal server error occurred.'}), 500

@app.route('/update-profile', methods=['POST'])

def update_profile():

    try:

        user_id = request.form.get('user_id')
        first_name = request.form.get('first_name')
        middle_name = request.form.get('middle_name', '')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')

        

        cur = get_cursor()

        

        if 'profile_picture' in request.files:

            file = request.files['profile_picture']

            _img_err = reject_non_image(file, 'profile_picture')

            if _img_err: return _img_err

            if file.filename != '':

                filename = secure_filename(f"profile_{user_id}_{file.filename}")

                # Convert FileStorage to bytes for Supabase

                file_content = file.read()

                

                # Upload to Supabase Storage

                bucket_name = "uploads"

                path_on_supa = f"avatars/{filename}"

                

                try:

                    # Upload file (upsert=True allows replacing if it already exists)

                    supabase.storage.from_(bucket_name).upload(

                        path=path_on_supa,

                        file=file_content,

                        file_options={"content-type": file.content_type, "upsert": "true"}

                    )

                    

                    # Get Public URL

                    public_url = supabase.storage.from_(bucket_name).get_public_url(path_on_supa)

                    

                    cur.execute("UPDATE users SET profile_picture=%s WHERE id=%s", (public_url, user_id))


                except Exception as storage_err:

                    print(f"STORAGE ERROR: {str(storage_err)}")

                    # Fallback to local filename just in case, or handle error

                    raise storage_err



        cur.execute("UPDATE users SET first_name=%s, middle_name=%s, last_name=%s, phone=%s WHERE id=%s", (first_name, middle_name, last_name, phone, user_id))

        # Update email if provided and not taken by another user
        new_email = request.form.get('email', '').strip().lower()
        if new_email and '@gmail.com' in new_email:
            cur.execute("SELECT id FROM users WHERE email=%s AND id != %s", (new_email, user_id))
            existing = cur.fetchone()
            if existing:
                return jsonify({"error": "This email is already used by another account."}), 409
            cur.execute("UPDATE users SET email=%s WHERE id=%s", (new_email, user_id))

        commit_db()

        

        return jsonify({"message": "Profile updated"}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()





@app.route('/toggle-favorite', methods=['POST'])

def toggle_favorite():

    data = request.json

    user_id = data.get('user_id')

    vehicle_id = data.get('vehicle_id')

    

    if not user_id or not vehicle_id:

        return jsonify({"error": "user_id and vehicle_id are required"}), 400

        

    try:

        cur = get_cursor()

        # Check if already exists

        cur.execute("SELECT * FROM favorites WHERE user_id = %s AND vehicle_id = %s", (user_id, vehicle_id))

        exists = cur.fetchone()

        

        if exists:

            cur.execute("DELETE FROM favorites WHERE user_id = %s AND vehicle_id = %s", (user_id, vehicle_id))

            message = "Removed from favorites"

            is_fav = False

        else:

            cur.execute("INSERT INTO favorites (user_id, vehicle_id) VALUES (%s, %s)", (user_id, vehicle_id))

            message = "Added to favorites"

            is_fav = True

            

        commit_db()

        return jsonify({"message": message, "is_favorite": is_fav}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/favorites', methods=['GET'])

def get_favorites():

    user_id = request.args.get('user_id')

    if not user_id:

        return jsonify({"error": "user_id is required"}), 400

        

    try:

        cur = get_cursor()

        cur.execute("""

            SELECT v.* FROM vehicles v

            JOIN favorites f ON v.id = f.vehicle_id

            WHERE f.user_id = %s

        """, (user_id,))

        vehicles = cur.fetchall()

        column_names = [desc[0] for desc in cur.description]

        result = [dict(zip(column_names, v)) for v in vehicles]

        return jsonify(result), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/review', methods=['POST'])

def add_review():

    data = request.json

    user_id = data.get('user_id')

    vehicle_id = data.get('vehicle_id')

    rating = data.get('rating')

    comment = data.get('comment')

    

    if not all([user_id, vehicle_id, rating]):

        return jsonify({"error": "user_id, vehicle_id, and rating are required"}), 400

        

    try:

        cur = get_cursor()

        cur.execute("""

            INSERT INTO reviews (user_id, vehicle_id, rating, comment)

            VALUES (%s, %s, %s, %s)

        """, (user_id, vehicle_id, rating, comment))

        commit_db()

        return jsonify({"message": "Review added successfully"}), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/reviews/<int:vehicle_id>', methods=['GET'])

def get_reviews(vehicle_id):

    try:

        cur = get_cursor()

        cur.execute("""

            SELECT r.*, u.full_name, u.profile_picture 

            FROM reviews r

            JOIN users u ON r.user_id = u.id

            WHERE r.vehicle_id = %s

            ORDER BY r.created_at DESC

        """, (vehicle_id,))

        reviews = cur.fetchall()

        column_names = [desc[0] for desc in cur.description]

        result = [dict(zip(column_names, r)) for r in reviews]

        return jsonify(result), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/saved-payment', methods=['POST'])

def save_payment():

    data = request.json

    user_id = data.get('user_id')

    card_type = data.get('card_type')

    last_four = data.get('last_four')

    provider = data.get('provider')

    

    if not all([user_id, card_type, last_four, provider]):

        return jsonify({"error": "Missing payment details"}), 400

        

    try:

        cur = get_cursor()

        cur.execute("""

            INSERT INTO saved_payments (user_id, card_type, last_four, provider)

            VALUES (%s, %s, %s, %s)

        """, (user_id, card_type, last_four, provider))

        commit_db()

        return jsonify({"message": "Payment method saved"}), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/saved-payments', methods=['GET'])

def get_saved_payments():

    user_id = request.args.get('user_id')

    if not user_id:

        return jsonify({"error": "user_id is required"}), 400

        

    try:

        cur = get_cursor()

        cur.execute("SELECT * FROM saved_payments WHERE user_id = %s", (user_id,))

        payments = cur.fetchall()

        column_names = [desc[0] for desc in cur.description]

        result = [dict(zip(column_names, p)) for p in payments]

        return jsonify(result), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/modify-booking', methods=['POST'])

def modify_booking():

    data = request.json

    booking_id = data.get('booking_id')

    new_start = data.get('start_date')

    new_end = data.get('end_date')

    preview = data.get('preview', False)

    

    if not all([booking_id, new_start, new_end]):

        return jsonify({"error": "booking_id, start_date, and end_date are required"}), 400

        

    try:

        cur = get_cursor()

        # Fetch current daily rate to recalculate total

        cur.execute("""

            SELECT b.total_price, v.daily_rate, b.status, b.amount_paid, b.payment_status,
                   b.addon_price, b.insurance_price, b.start_date AS old_start, b.end_date AS old_end
            FROM bookings b 
            JOIN vehicles v ON b.vehicle_id = v.id 
            WHERE b.id = %s
        """, (booking_id,))

        bk = cur.fetchone()

        

        if not bk or bk['status'] not in ['Pending', 'Confirmed']:

            return jsonify({"error": "Booking cannot be modified"}), 400

        # ── Overlap guard for modification: check no other booking occupies the new dates ──
        cur.execute("""
            SELECT b.id, b.start_date, b.end_date, b.status,
                   (b.end_date + INTERVAL '1 day')::date AS next_available
            FROM bookings b
            JOIN bookings orig ON orig.id = %s
            WHERE b.vehicle_id = orig.vehicle_id
              AND b.id != %s
              AND b.status IN ('Pending', 'Confirmed', 'Approved', 'Picked Up', 'Ongoing')
              AND b.start_date <= %s
              AND b.end_date >= %s
            ORDER BY b.start_date ASC
            LIMIT 1
        """, (booking_id, booking_id, new_end, new_start))

        mod_overlap = cur.fetchone()
        if mod_overlap:
            o = dict(mod_overlap)
            return jsonify({
                "error": "Cannot change dates – another booking occupies {start} to {end} (status: {status}). "
                         "The vehicle is available again from {next}.".format(
                             start=str(o['start_date']), end=str(o['end_date']),
                             status=o['status'], next=str(o['next_available']))
            }), 409

            

        rate = float(bk['daily_rate'])

        # Calculate new days
        from datetime import datetime
        d1 = datetime.strptime(new_start, "%Y-%m-%d")
        d2 = datetime.strptime(new_end, "%Y-%m-%d")
        new_days = (d2 - d1).days + 1

        if new_days <= 0:
            return jsonify({"error": "Invalid dates"}), 400

        # Calculate old days to find out daily rate of addons and insurance
        od1 = datetime.strptime(str(bk['old_start']).split(' ')[0], "%Y-%m-%d")
        od2 = datetime.strptime(str(bk['old_end']).split(' ')[0], "%Y-%m-%d")
        old_days = (od2 - od1).days + 1

        daily_addon = float(bk['addon_price'] or 0) / old_days if old_days > 0 else 0
        daily_insurance = float(bk['insurance_price'] or 0) / old_days if old_days > 0 else 0

        new_addon_price = daily_addon * new_days
        new_insurance_price = daily_insurance * new_days
        new_base_price = rate * new_days

        new_total = new_base_price + new_addon_price + new_insurance_price

        # Check for long term discount in settings table
        cur.execute("SELECT value FROM settings WHERE key = 'long_term_discount_days'")
        row = cur.fetchone()
        lt_days = int(row['value']) if row else 7
        
        cur.execute("SELECT value FROM settings WHERE key = 'long_term_discount_percent'")
        row = cur.fetchone()
        lt_pct = int(row['value']) if row else 10
        
        discount = 0
        if new_days >= lt_days:
            # apply discount to base_price, mirroring frontend calculation
            discount = new_base_price * (lt_pct / 100.0)

        new_total -= discount

        if preview:
            return jsonify({"new_total": float(f"{new_total:.2f}")}), 200
            
        amount_paid = float(bk['amount_paid'] or 0)
        new_balance = new_total - amount_paid
        
        new_payment_status = bk['payment_status']
        if new_balance > 0:
            if amount_paid > 0:
                new_payment_status = 'Partially Paid'
            else:
                new_payment_status = 'Unpaid'
        elif new_balance <= 0:
            new_payment_status = 'Paid'
            new_balance = 0.0

        cur.execute("""
            UPDATE bookings 
            SET start_date = %s, end_date = %s, total_price = %s, base_price = %s, 
                addon_price = %s, insurance_price = %s, discount_amount = %s,
                balance_amount = %s, payment_status = %s
            WHERE id = %s
        """, (new_start, new_end, new_total, new_base_price, new_addon_price, 
              new_insurance_price, discount, new_balance, new_payment_status, booking_id))

        commit_db()

        # Send in-app notification to customer
        try:
            cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))
            bk_row = cur.fetchone()
            if bk_row:
                from notifications import notification_service
                notification_service.notify_user(
                    bk_row['user_id'],
                    "Booking Updated",
                    f"Your booking #{booking_id} dates have been updated: {new_start} to {new_end}. New total: PHP {round(new_total, 2)}.",
                    'booking_modified'
                )
        except Exception as notif_err:
            print(f"ERROR SENDING MODIFY BOOKING NOTIFICATION: {notif_err}")

        return jsonify({"message": "Booking modified", "new_total": float(f"{new_total:.2f}"), "new_balance": float(f"{new_balance:.2f}")}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()





@app.route('/split-bill/request', methods=['POST'])

def request_split_bill():

    data = request.json

    booking_id = data.get('booking_id')

    partner_email = data.get('partner_email')

    amount = data.get('amount')

    

    if not all([booking_id, partner_email, amount]):

        return jsonify({"error": "Missing split bill details"}), 400

        

    try:

        cur = get_cursor()

        

        # Check if partner exists

        cur.execute("SELECT id FROM users WHERE email=%s", (partner_email,))

        if not cur.fetchone():

             return jsonify({"error": "Partner email not found in our system."}), 404



        cur.execute("""

            INSERT INTO split_payments (booking_id, partner_email, amount, status)

            VALUES (%s, %s, %s, 'Pending')

        """, (booking_id, partner_email, amount))

        

        cur.execute("UPDATE bookings SET split_status = 'Pending Split', split_with_email = %s WHERE id = %s", (partner_email, booking_id))

        commit_db()

        # Send SMS to partner with split request details
        try:
            # Look up partner user_id by email
            cur.execute("SELECT id FROM users WHERE email = %s", (partner_email,))
            partner_row = cur.fetchone()
            # Look up initiator name from the booking
            cur.execute(
                "SELECT u.full_name FROM bookings b JOIN users u ON b.user_id = u.id WHERE b.id = %s",
                (booking_id,)
            )
            initiator_row = cur.fetchone()
            initiator_name = initiator_row['full_name'] if initiator_row else 'A user'
            if partner_row:
                notification_service.notify_user(
                    partner_row['id'],
                    "Split Payment Request",
                    f"{initiator_name} has requested a split payment for booking #{booking_id}. Your share: PHP {float(amount)}.",
                    'split_request'
                )
        except Exception as notif_err:
            print(f"ERROR SENDING SPLIT REQUEST NOTIFICATION: {notif_err}")

        return jsonify({"message": "Split bill request sent successfully."}), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/split-bills', methods=['GET'])

def get_split_bills():

    user_email = request.args.get('email')

    if not user_email:

        return jsonify({"error": "email is required"}), 400

        

    try:

        cur = get_cursor()

        query = """

            SELECT sp.id as split_id, sp.amount, sp.status, 

                   b.id as booking_id, b.start_date, b.end_date, 

                   v.brand, v.model, u.full_name as initiator_name

            FROM split_payments sp

            JOIN bookings b ON sp.booking_id = b.id

            JOIN vehicles v ON b.vehicle_id = v.id

            JOIN users u ON b.user_id = u.id

            WHERE sp.partner_email = %s

        """

        cur.execute(query, (user_email,))

        data = cur.fetchall()

        

        splits = [dict(row) for row in data]

        return jsonify(splits), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/split-bill/pay', methods=['POST'])

def pay_split_bill():

    data = request.json

    split_id = data.get('split_id')

    

    if not split_id:

         return jsonify({"error": "split_id required"}), 400

         

    try:

        cur = get_cursor()

        # Mark split as paid

        cur.execute("UPDATE split_payments SET status = 'Paid' WHERE id = %s", (split_id,))

        

        # Check if all splits for this booking are paid

        cur.execute("SELECT booking_id FROM split_payments WHERE id = %s", (split_id,))

        b_id = cur.fetchone()

        if b_id:

             cur.execute("UPDATE bookings SET split_status = 'Completed Split' WHERE id = %s", (b_id['booking_id'],))

             

        commit_db()

        # Send SMS to booking initiator about the split payment
        try:
            if b_id:
                # Fetch amount paid and booking initiator user_id
                cur.execute(
                    "SELECT amount FROM split_payments WHERE id = %s",
                    (split_id,)
                )
                sp_row = cur.fetchone()
                cur.execute(
                    "SELECT user_id FROM bookings WHERE id = %s",
                    (b_id['booking_id'],)
                )
                bk_row = cur.fetchone()
                if sp_row and bk_row:
                    notification_service.notify_user(
                        bk_row['user_id'],
                        "Split Payment Received",
                        f"Your split payment partner has paid PHP {float(sp_row['amount'])} for booking #{b_id['booking_id']}.",
                        'split_paid'
                    )
        except Exception as notif_err:
            print(f"ERROR SENDING SPLIT PAID NOTIFICATION: {notif_err}")

        return jsonify({"message": "Split bill paid successfully."}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



# ==================== ADMIN BOOKING MANAGEMENT ====================



@app.route('/bookings', methods=['GET'])

def get_all_bookings():

    """Get all bookings with customer, vehicle, and driver info for admin panel."""

    admin_id = request.args.get('admin_id')

    try:

        try:
            from routers.paymongo_routes import check_and_update_unpaid_paymongo_bookings
            check_and_update_unpaid_paymongo_bookings()
        except Exception as pm_err:
            print(f"Auto status check error for admin: {pm_err}")

        cur = get_cursor()

        

        # Determine location filter

        location_filter = None

        if admin_id:

            cur.execute("SELECT role, assigned_location FROM users WHERE id = %s", (admin_id,))

            admin = cur.fetchone()

            if admin and admin['role'] == 'admin' and admin['assigned_location']:

                location_filter = admin['assigned_location']



        query = """

            SELECT b.id, u.full_name AS customer_name, u.email AS customer_email,

                   CONCAT(v.brand, ' ', v.model, ' (', v.plate_number, ')') AS car,
                   v.plate_number,

                   b.start_date, b.end_date, b.total_price, b.status,

                   b.payment_status, b.base_price, b.addon_price, b.insurance_price,
                   b.insurance_type, b.discount_amount, b.payment_type,
                   b.amount_paid, b.balance_amount,

                   b.pickup_location, b.rental_type, b.addons,

                   b.driver_id, d.full_name AS driver_name,

                   pm.method AS payment_method, pm.reference_number,

                   b.refund_amount, b.refund_channel, b.refund_account_name, b.refund_account_number,
                   b.refund_proof_url, b.refund_ref, b.refunded_at,

                   COALESCE(ld.full_name, u.full_name) AS license_full_name,
                   COALESCE(ld.license_number, u.license_number) AS license_number,
                   COALESCE(CAST(ld.expiry_date AS TEXT), CAST(u.license_expiry AS TEXT)) AS license_expiry,
                   ld.license_class,
                   ld.license_front_url,
                   ld.license_back_url,
                   ld.emergency_contact_name,
                   ld.emergency_contact_phone,
                   ld.emergency_contact_relationship

            FROM bookings b

            JOIN users u ON b.user_id = u.id

            JOIN vehicles v ON b.vehicle_id = v.id

            LEFT JOIN drivers d ON b.driver_id = d.id

            LEFT JOIN license_details ld ON b.user_id = ld.user_id

            LEFT JOIN (
                SELECT booking_id, method, reference_number
                FROM payments
                WHERE id IN (SELECT MAX(id) FROM payments GROUP BY booking_id)
            ) pm ON pm.booking_id = b.id

        """

        

        params = []

        if location_filter:

            query += " WHERE b.pickup_location = %s "

            params.append(location_filter)

            

        query += " ORDER BY b.id DESC"

        

        cur.execute(query, tuple(params))

        data = cur.fetchall()

        bookings = [dict(row) for row in data]

        return jsonify(bookings), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()


@app.route('/bookings/cancelled', methods=['GET'])
def get_cancelled_bookings():
    """Get all cancelled bookings with pagination and sorting for admin panel."""
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 25))
        sort_by = request.args.get('sort_by', 'cancellation_date_desc')
        
        # Validate page_size
        if page_size not in [10, 25, 50, 100]:
            page_size = 25
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Determine sort order
        sort_clause = "b.created_at DESC"  # Default: cancellation date descending
        if sort_by == 'cancellation_date_asc':
            sort_clause = "b.created_at ASC"
        elif sort_by == 'customer_name':
            sort_clause = "u.full_name ASC"
        elif sort_by == 'original_booking_date':
            sort_clause = "b.created_at DESC"
        
        cur = get_cursor()
        
        # Get total count of cancelled bookings
        cur.execute("""
            SELECT COUNT(*) as total
            FROM bookings b
            WHERE b.status = 'Cancelled' OR b.status = 'Rejected'
        """)
        total_count = cur.fetchone()['total']
        
        # Get cancelled bookings with pagination
        query = f"""
            SELECT b.id, u.full_name AS customer_name, b.user_id,
                   CONCAT(v.brand, ' ', v.model, ' (', v.plate_number, ')') AS car,
                   b.start_date, b.end_date, b.total_price, b.status,
                   b.created_at AS booking_date,
                   b.created_at AS cancellation_date,
                   b.cancellation_reason,
                   b.cancelled_by,
                   b.payment_status
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN vehicles v ON b.vehicle_id = v.id
            WHERE b.status = 'Cancelled' OR b.status = 'Rejected'
            ORDER BY {sort_clause}
            LIMIT %s OFFSET %s
        """
        
        cur.execute(query, (page_size, offset))
        data = cur.fetchall()
        bookings = [dict(row) for row in data]
        
        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size
        
        return jsonify({
            'bookings': bookings,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total_count,
                'total_pages': total_pages
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()


@app.route('/admin/bookings/<int:booking_id>/assign_driver', methods=['PUT'])

def assign_booking_driver(booking_id):

    """Assign an approved driver to a confirmed/pending booking."""

    data = request.json

    driver_id = data.get('driver_id')

    if not driver_id:

        return jsonify({"error": "driver_id is required"}), 400



    try:

        cur = get_cursor()

        

        # Verify driver is approved

        cur.execute("SELECT status FROM drivers WHERE id=%s", (driver_id,))

        drv = cur.fetchone()

        if not drv or drv['status'] != 'Approved':

            return jsonify({"error": "Selected driver is invalid or not approved."}), 400



        # Update booking

        cur.execute("UPDATE bookings SET driver_id=%s WHERE id=%s", (driver_id, booking_id))

        commit_db()

        return jsonify({"message": "Driver successfully assigned.", "booking_id": booking_id}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/bookings/<int:booking_id>/approve', methods=['PUT'])

def approve_booking(booking_id):

    """Approve a pending booking."""

    try:

        cur = get_cursor()

        cur.execute("SELECT status FROM bookings WHERE id=%s", (booking_id,))

        row = cur.fetchone()

        if not row:

            return jsonify({"error": "Booking not found"}), 404

        if row['status'] != 'Pending':

            return jsonify({"error": f"Cannot approve a booking with status '{row['status']}'"}), 400

        cur.execute("UPDATE bookings SET status='Approved' WHERE id=%s", (booking_id,))

        # If booking was pending payment (cash), mark it as Paid and create payment record
        cur.execute("SELECT payment_status, total_price FROM bookings WHERE id=%s", (booking_id,))
        pay_row = cur.fetchone()
        if pay_row and pay_row['payment_status'] in ('Pending Payment', 'Unpaid'):
            total = float(pay_row.get('total_price') or 0)
            cur.execute("""
                UPDATE bookings
                SET payment_status = 'Paid', amount_paid = %s, balance_amount = 0
                WHERE id = %s
            """, (total, booking_id))
            # Insert a payment record
            try:
                cur.execute("""
                    INSERT INTO payments (booking_id, amount, method, reference_number, status)
                    VALUES (%s, %s, 'Cash (Over the counter)', 'CASH-CONFIRMED', 'Completed')
                """, (booking_id, total))
            except Exception:
                pass  # Don't block approval if payment insert fails


        

        # Ensure vehicle status is 'Booked'

        cur.execute("UPDATE vehicles SET status='Booked' WHERE id=(SELECT vehicle_id FROM bookings WHERE id=%s)", (booking_id,))

        

        commit_db()

        

        # Send SMS notification
        cur.execute(
            """SELECT b.user_id, v.brand, v.model, b.start_date
               FROM bookings b
               JOIN vehicles v ON b.vehicle_id = v.id
               WHERE b.id = %s""",
            (booking_id,)
        )
        b_data = cur.fetchone()
        if b_data:
            notification_service.notify_user(
                b_data['user_id'],
                "Booking Approved",
                f"Good news! Booking #{booking_id} for {b_data['brand']} {b_data['model']} starting {b_data['start_date']} has been approved.",
                'booking_approved'
            )

            

        # Log activity

        log_activity(

            admin_id=request.args.get('admin_id', 0),

            admin_name="Administrator",

            action='APPROVE_BOOKING',

            target_type='BOOKING',

            target_id=str(booking_id),

            details=f"Approved booking #{booking_id}"

        )



        return jsonify({"message": "Booking approved", "booking_id": booking_id}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/bookings/<int:booking_id>/mark-no-show', methods=['POST'])
def mark_no_show(booking_id):
    """Mark a booking as No Show. Full forfeit if Paid; cancel if Unpaid."""
    try:
        from datetime import datetime, timezone, timedelta
        PH = timezone(timedelta(hours=8))
        now_ph = datetime.now(tz=PH)

        cur = get_cursor()
        cur.execute("""
            SELECT b.id, b.status, b.payment_status, b.vehicle_id, b.user_id,
                   b.start_date, b.start_time, COALESCE(u.full_name, 'Unknown') as customer_name
            FROM bookings b
            LEFT JOIN users u ON b.user_id = u.id
            WHERE b.id = %s
        """, (booking_id,))
        bk = cur.fetchone()
        if not bk:
            return jsonify({"error": "Booking not found."}), 404

        st = (bk['status'] or '').lower()
        if st not in ('confirmed', 'approved'):
            return jsonify({"error": f"Cannot mark as No Show — booking status is '{bk['status']}'."}), 409

        # Verify pickup time has already passed
        pickup_date = bk['start_date']
        if hasattr(pickup_date, 'date'):
            pickup_date = pickup_date.date()
        pickup_time_raw = bk.get('start_time') or '06:00'
        if hasattr(pickup_time_raw, 'strftime'):
            pickup_time_str = pickup_time_raw.strftime('%H:%M')
        else:
            pickup_time_str = str(pickup_time_raw)[:5]
        try:
            ph_hour, ph_min = map(int, pickup_time_str.split(':'))
        except Exception:
            ph_hour, ph_min = 6, 0
        pickup_dt = datetime(pickup_date.year, pickup_date.month, pickup_date.day, ph_hour, ph_min, tzinfo=PH)
        if now_ph < pickup_dt:
            fmt = pickup_dt.strftime('%B %d, %Y at %I:%M %p')
            return jsonify({"error": f"Cannot mark as No Show before the scheduled pickup time ({fmt})."}), 409

        # Mark booking as No Show
        cur.execute("UPDATE bookings SET status = 'No Show' WHERE id = %s", (booking_id,))

        # Release vehicle
        if bk['vehicle_id']:
            cur.execute("UPDATE vehicles SET status = 'Available' WHERE id = %s", (bk['vehicle_id'],))

        # Refund policy: Paid → full forfeit (keep Paid), Unpaid → set to Cancelled
        if (bk['payment_status'] or '').lower() not in ('paid',):
            cur.execute("UPDATE bookings SET payment_status = 'Cancelled' WHERE id = %s", (booking_id,))

        commit_db()

        # Notify customer in-app
        if bk['user_id']:
            try:
                notification_service.notify_user(
                    bk['user_id'],
                    "Booking Marked as No Show",
                    f"Your booking #{booking_id} has been marked as No Show because you did not arrive at the scheduled pickup time. "
                    + ("Your payment has been forfeited per our no-show policy." if (bk['payment_status'] or '').lower() == 'paid' else "No charge was applied."),
                    'no_show'
                )
            except Exception as n_err:
                print(f"[mark_no_show] customer notify error: {n_err}")

        # Notify all admins in-app
        try:
            notification_service.notify_admins_inapp(
                f"🚫 No Show: Booking #{booking_id}",
                f"Booking #{booking_id} for '{bk['customer_name']}' has been marked as No Show by admin.",
                'no_show_alert',
                type='no_show_alert',
                booking_id=booking_id
            )
        except Exception as n_err:
            print(f"[mark_no_show] admin notify error: {n_err}")

        return jsonify({"message": "Booking marked as No Show.", "booking_id": booking_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()


@app.route('/inspections/submit', methods=['POST'])
def submit_inspection():
    """Submit a vehicle inspection (pickup or return)."""
    try:
        booking_id = request.form.get('booking_id')
        inspection_type = request.form.get('inspection_type') # 'pickup' or 'return'
        mileage = request.form.get('mileage')
        fuel_level = request.form.get('fuel_level')
        notes = request.form.get('notes')
        inspector_id = request.form.get('inspector_id')
        
        if not booking_id or not inspection_type:
            return jsonify({"error": "Missing required fields"}), 400

        cur = get_cursor()

        # Fetch booking details first to validate status & dates
        cur.execute("SELECT start_date, start_time, end_date, end_time, service_type, vehicle_id, status FROM bookings WHERE id = %s", (booking_id,))
        bk = cur.fetchone()
        if not bk:
            return jsonify({"error": "Booking not found."}), 404

        b_status = (bk.get('status') or '').strip().lower()

        # Guard: Cannot inspect cancelled or no-show bookings
        if b_status in ('cancelled', 'no show', 'noshow', 'rejected'):
            return jsonify({"error": f"Cannot submit inspection for a booking marked as '{bk.get('status')}'. Please update booking status first."}), 400

        from datetime import datetime, timezone, timedelta, date
        PH = timezone(timedelta(hours=8))
        now_ph = datetime.now(tz=PH)

        if inspection_type == 'pickup':
            # ── Guard 1: pickup datetime not yet reached (allow 1 hour before) ──
            pickup_date = bk['start_date']
            if isinstance(pickup_date, str):
                try:
                    pickup_date = datetime.strptime(pickup_date[:10], '%Y-%m-%d').date()
                except Exception:
                    pickup_date = None
            elif hasattr(pickup_date, 'date'):
                pickup_date = pickup_date.date()

            if pickup_date:
                pickup_time_str = bk.get('start_time') or '06:00'
                if hasattr(pickup_time_str, 'strftime'):
                    pickup_time_str = pickup_time_str.strftime('%H:%M')
                try:
                    ph_hour, ph_min = map(int, str(pickup_time_str)[:5].split(':'))
                except Exception:
                    ph_hour, ph_min = 6, 0

                pickup_dt = datetime(pickup_date.year, pickup_date.month, pickup_date.day, ph_hour, ph_min, tzinfo=PH)
                allow_from = pickup_dt - timedelta(hours=1)

                if now_ph < allow_from:
                    fmt_time = pickup_dt.strftime('%I:%M %p')
                    fmt_allow = allow_from.strftime('%I:%M %p')
                    return jsonify({
                        "error": f"Pickup inspection can be done starting at {fmt_allow} (1 hour before scheduled pickup on {pickup_dt.strftime('%B %d, %Y')} at {fmt_time})."
                    }), 409

            # ── Guard 2: same vehicle already picked up by another booking ─
            vehicle_id = bk['vehicle_id']
            if vehicle_id:
                cur.execute("""
                    SELECT id FROM bookings
                    WHERE vehicle_id = %s
                      AND id != %s
                      AND LOWER(status) IN ('picked up', 'ongoing')
                """, (vehicle_id, booking_id))
                conflict = cur.fetchone()
                if conflict:
                    return jsonify({
                        "error": f"This vehicle is currently in use by Booking #{conflict['id']}. It must be returned first before it can be picked up for another booking."
                    }), 409

        # Handle photos upload
        photo_urls = []
        if 'photos' in request.files:
            files = request.files.getlist('photos')
            for file in files:
                if file.filename != '':
                    filename = f"inspect_{booking_id}_{inspection_type}_{int(datetime.now().timestamp())}_{secure_filename(file.filename)}"
                    file_data = file.read()
                    supabase.storage.from_('uploads').upload(
                        path=filename,
                        file=file_data,
                        file_options={"content-type": file.content_type}
                    )
                    url = supabase.storage.from_('uploads').get_public_url(filename)
                    photo_urls.append(url)

        # Save to database only after all guards pass
        import json
        cur.execute("""
            INSERT INTO vehicle_inspections (booking_id, inspection_type, photos, mileage, fuel_level, notes, inspector_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (booking_id, inspection_type, json.dumps(photo_urls), mileage, fuel_level, notes, inspector_id))
        
        inspection_id = cur.fetchone()['id']

        # Auto-update booking and vehicle status based on inspection type
        vehicle_id = bk['vehicle_id']
        if inspection_type == 'pickup':
            cur.execute("UPDATE bookings SET status = 'Picked Up' WHERE id = %s", (booking_id,))
            if vehicle_id:
                cur.execute("UPDATE vehicles SET status = 'Rented' WHERE id = %s", (vehicle_id,))
            
            # Late Pickup Time Deduction Logic
            s_type = (bk.get('service_type') or 'pickup').strip().lower()
            if s_type == 'pickup':
                pickup_date = bk['start_date']
                if isinstance(pickup_date, str):
                    try:
                        pickup_date = datetime.strptime(pickup_date[:10], '%Y-%m-%d').date()
                    except Exception:
                        pickup_date = None
                elif hasattr(pickup_date, 'date'):
                    pickup_date = pickup_date.date()

                if pickup_date:
                    pickup_time_str = bk.get('start_time') or '06:00'
                    if hasattr(pickup_time_str, 'strftime'):
                        pickup_time_str = pickup_time_str.strftime('%H:%M')
                    try:
                        ph_hour, ph_min = map(int, str(pickup_time_str)[:5].split(':'))
                    except Exception:
                        ph_hour, ph_min = 6, 0

                    scheduled_pickup_dt = datetime(pickup_date.year, pickup_date.month, pickup_date.day, ph_hour, ph_min, tzinfo=PH)
                    
                    if now_ph > scheduled_pickup_dt:
                        late_duration = now_ph - scheduled_pickup_dt
                        
                        # Fetch original end datetime
                        end_date = bk['end_date']
                        if isinstance(end_date, str):
                            try:
                                end_date = datetime.strptime(end_date[:10], '%Y-%m-%d').date()
                            except Exception:
                                end_date = None
                        elif hasattr(end_date, 'date'):
                            end_date = end_date.date()

                        if end_date:
                            end_time_str = bk.get('end_time') or '06:00'
                            if hasattr(end_time_str, 'strftime'):
                                end_time_str = end_time_str.strftime('%H:%M')
                            try:
                                end_hour, end_min = map(int, str(end_time_str)[:5].split(':'))
                            except Exception:
                                end_hour, end_min = 6, 0

                            scheduled_end_dt = datetime(end_date.year, end_date.month, end_date.day, end_hour, end_min, tzinfo=PH)
                            new_end_dt = scheduled_end_dt - late_duration
                            
                            # Limit new end datetime to be at least now_ph
                            if new_end_dt < now_ph:
                                new_end_dt = now_ph

                            new_end_date_str = new_end_dt.strftime('%Y-%m-%d')
                            new_end_time_str = new_end_dt.strftime('%H:%M')

                            cur.execute("""
                                UPDATE bookings 
                                SET end_date = %s, end_time = %s 
                                WHERE id = %s
                            """, (new_end_date_str, new_end_time_str, booking_id))
                            print(f"[submit_inspection] Late pickup detected. Deducted {late_duration.total_seconds() / 3600:.2f} hours. New end datetime: {new_end_date_str} {new_end_time_str}")
        elif inspection_type == 'return':
            cur.execute("UPDATE bookings SET status = 'Completed' WHERE id = %s", (booking_id,))
            if vehicle_id:
                cur.execute("UPDATE vehicles SET status = 'Available' WHERE id = %s", (vehicle_id,))

        # ── Auto-update Vehicle Master Odometer and Fuel Level ──
        distance_driven = None
        if vehicle_id:
            try:
                if mileage and str(mileage).strip().isdigit() and int(mileage) >= 0:
                    new_odom = int(mileage)
                    cur.execute("UPDATE vehicles SET odometer = %s WHERE id = %s", (new_odom, vehicle_id))
                if fuel_level and str(fuel_level).strip():
                    cur.execute("UPDATE vehicles SET fuel_level = %s WHERE id = %s", (str(fuel_level).strip(), vehicle_id))
            except Exception as _ve:
                print(f"[submit_inspection] Vehicle master update warning: {_ve}")

            if inspection_type == 'return':
                try:
                    cur.execute("SELECT mileage FROM vehicle_inspections WHERE booking_id = %s AND inspection_type = 'pickup' ORDER BY id DESC LIMIT 1", (booking_id,))
                    p_row = cur.fetchone()
                    if p_row and p_row['mileage'] and str(p_row['mileage']).strip().isdigit() and mileage and str(mileage).strip().isdigit():
                        p_mileage = int(p_row['mileage'])
                        r_mileage = int(mileage)
                        if r_mileage >= p_mileage:
                            distance_driven = r_mileage - p_mileage
                except Exception as _de:
                    print(f"[submit_inspection] Distance calc warning: {_de}")

                # Low Fuel / Maintenance Warnings push notifications to Admins
                try:
                    is_low_fuel = False
                    if fuel_level:
                        fl_lower = str(fuel_level).strip().lower()
                        if fl_lower in ('empty', '1/4', 'low', 'quarter') or 'empty' in fl_lower or '1/4' in fl_lower:
                            is_low_fuel = True
                    
                    is_due_maintenance = False
                    cur.execute("SELECT name, next_service_schedule, odometer FROM vehicles WHERE id = %s", (vehicle_id,))
                    veh_info = cur.fetchone()
                    if veh_info:
                        svc_date = veh_info['next_service_schedule']
                        if svc_date:
                            from datetime import timedelta, date
                            if isinstance(svc_date, str):
                                try:
                                    svc_date = datetime.strptime(svc_date[:10], '%Y-%m-%d').date()
                                except Exception:
                                    svc_date = None
                            elif hasattr(svc_date, 'date'):
                                svc_date = svc_date.date()
                            
                            # Alert if next service is within 7 days or past
                            if svc_date and svc_date <= (datetime.now().date() + timedelta(days=7)):
                                is_due_maintenance = True

                        v_name = veh_info['name'] or f"Vehicle #{vehicle_id}"
                        from notifications import notification_service
                        if is_low_fuel:
                            notification_service.notify_admins_inapp(
                                "⛽ Low Fuel Alert",
                                f"Vehicle '{v_name}' (Odometer: {mileage} km) was returned with low fuel level: {fuel_level}.",
                                'admin_low_fuel_alert',
                                type='admin_low_fuel_alert',
                                booking_id=booking_id
                            )
                        if is_due_maintenance:
                            notification_service.notify_admins_inapp(
                                "🔧 Maintenance Schedule Alert",
                                f"Vehicle '{v_name}' is due for maintenance. Next service date: {veh_info['next_service_schedule']}.",
                                'admin_maintenance_alert',
                                type='admin_maintenance_alert',
                                booking_id=booking_id
                            )
                except Exception as warning_err:
                    print(f"[submit_inspection] Warnings check error: {warning_err}")

        commit_db()

        res_payload = {
            "message": "Inspection submitted successfully",
            "id": inspection_id,
            "updated_odometer": mileage,
            "updated_fuel_level": fuel_level
        }
        if distance_driven is not None:
            res_payload["distance_driven"] = distance_driven

        return jsonify(res_payload), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()







def get_inspections(booking_id):

    """Get all inspections for a booking."""

    try:

        cur = get_cursor()

        cur.execute("SELECT * FROM vehicle_inspections WHERE booking_id = %s ORDER BY created_at ASC", (booking_id,))

        inspections = cur.fetchall()

        return jsonify([dict(i) for i in inspections]), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/cancel-booking', methods=['POST'])

def user_cancel_booking():

    """Allow a user to cancel their own booking. Applies 20% non-refundable fee if < 48h before pickup."""

    try:

        data = request.get_json(silent=True) or {}
        booking_id = data.get('booking_id')
        user_id    = data.get('user_id')
        reason     = data.get('reason', 'No reason provided')

        cur = get_cursor()
        cur.execute("""
            SELECT user_id, status, vehicle_id, start_date,
                   amount_paid, total_price, payment_status, points_redeemed
            FROM bookings WHERE id = %s
        """, (booking_id,))
        booking = cur.fetchone()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        if user_id and int(booking['user_id']) != int(user_id):
            return jsonify({"error": "Unauthorized. You can only cancel your own bookings."}), 403

        if booking['status'] not in ['Pending', 'Confirmed', 'Approved']:
            return jsonify({"error": f"Cannot cancel a booking that is '{booking['status']}'"}), 400

        # ?? 48-hour cancellation policy ??????????????????????????????????
        import datetime as _dtm
        amount_paid = float(booking.get('amount_paid') or booking.get('total_price') or 0)
        refund_amount = 0.0
        non_refundable_fee = 0.0
        new_payment_status = 'Cancelled'

        if booking['status'] == 'Confirmed' and amount_paid > 0:
            # Parse pickup date
            start_raw = booking['start_date']
            if isinstance(start_raw, (_dtm.date, _dtm.datetime)):
                pickup_dt = _dtm.datetime.combine(start_raw if isinstance(start_raw, _dtm.date) else start_raw.date(),
                                                   _dtm.time(6, 0))
            else:
                pickup_dt = _dtm.datetime.strptime(str(start_raw)[:10], '%Y-%m-%d').replace(hour=6)

            hours_until_pickup = (pickup_dt - _dtm.datetime.now()).total_seconds() / 3600

            if hours_until_pickup >= 48:
                # Full refund
                refund_amount = amount_paid
                non_refundable_fee = 0.0
                new_payment_status = 'Refund Pending'
            else:
                # 20% non-refundable reservation fee
                non_refundable_fee = round(amount_paid * 0.20, 2)
                refund_amount = round(amount_paid - non_refundable_fee, 2)
                new_payment_status = 'Refund Pending' if refund_amount > 0 else 'Cancelled'
        # ?????????????????????????????????????????????????????????????????

        # Ensure refund columns exist
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_amount NUMERIC(12,2)")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_note TEXT")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ")
        commit_db()

        cur.execute("""
            UPDATE bookings
            SET status = 'Cancelled',
                payment_status = %s,
                cancellation_reason = %s,
                cancelled_by = 'customer',
                cancelled_at = NOW(),
                refund_amount = %s,
                refund_note = %s
            WHERE id = %s
        """, (new_payment_status, reason,
              refund_amount if refund_amount > 0 else None,
              f"Non-refundable fee: PHP {non_refundable_fee:.2f} (cancelled < 48h before pickup)" if non_refundable_fee > 0 else None,
              booking_id))

        if booking['vehicle_id']:
            cur.execute("UPDATE vehicles SET status = 'Available' WHERE id = %s", (booking['vehicle_id'],))

        # Refund redeemed loyalty points
        redeemed = int(booking.get('points_redeemed', 0) or 0)
        if redeemed > 0:
            cur.execute("UPDATE users SET loyalty_points = loyalty_points + %s WHERE id = %s", (redeemed, booking['user_id']))

        commit_db()

        # Notifications
        try:
            if refund_amount > 0:
                notif_msg = (f"Booking #{booking_id} cancelled. "
                             f"Refund of PHP {refund_amount:,.2f} will be processed."
                             + (f" Note: 20% reservation fee (PHP {non_refundable_fee:,.2f}) is non-refundable as cancelled < 48h before pickup." if non_refundable_fee > 0 else ""))
            else:
                notif_msg = f"Booking #{booking_id} cancelled. No refund applicable."
            notification_service.notify_user(booking['user_id'], "Booking Cancelled", notif_msg, 'booking_cancelled')
        except Exception:
            pass

        # Notify admins about the cancellation
        try:
            _cur_cn = get_cursor()
            _cur_cn.execute("SELECT full_name FROM users WHERE id = %s", (booking['user_id'],))
            _urow = _cur_cn.fetchone()
            _uname = _urow['full_name'] if _urow else f'User #{booking["user_id"]}'
            _admin_msg = f"Booking #{booking_id} cancelled by customer {_uname}. Reason: {reason}."
            if refund_amount > 0:
                _admin_msg += f" Refund of PHP {refund_amount:,.2f} is pending."
            notification_service.notify_admins_inapp(
                "Booking Cancelled by Customer",
                _admin_msg,
                'admin_booking_cancelled',
                type='admin_booking_cancelled',
                booking_id=booking_id
            )
            
            # Also notify admins of the refund request if there's a refund pending
            if refund_amount > 0:
                notification_service.notify_admins_inapp(
                    "Refund Request",
                    f"Refund request of PHP {refund_amount:,.2f} for cancelled booking #{booking_id} by {_uname}.",
                    'admin_refund_request',
                    type='admin_refund_request',
                    booking_id=booking_id
                )
        except Exception as _admin_err:
            print(f"Admin cancel notification error: {_admin_err}")

        return jsonify({
            "message": "Booking cancelled successfully.",
            "refund_amount": refund_amount,
            "non_refundable_fee": non_refundable_fee,
            "refund_status": new_payment_status
        }), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/bookings/<int:booking_id>/reject', methods=['PUT'])

def reject_booking(booking_id):

    """Reject a pending booking."""

    try:

        cur = get_cursor()

        cur.execute("SELECT status, vehicle_id, user_id, points_redeemed FROM bookings WHERE id=%s", (booking_id,))
        row = cur.fetchone()
        
        if not row:
            return jsonify({"error": "Booking not found"}), 404
            
        if row['status'] != 'Pending':
            return jsonify({"error": f"Cannot reject a booking with status '{row['status']}'"}), 400

        cur.execute("UPDATE bookings SET status='Rejected' WHERE id=%s", (booking_id,))

        # Refund redeemed loyalty points
        redeemed = int(row.get('points_redeemed', 0) or 0)
        if redeemed > 0:
            cur.execute("UPDATE users SET loyalty_points = loyalty_points + %s WHERE id = %s", (redeemed, row['user_id']))

        commit_db()

        

        # Send in-app notification
        notification_service.notify_user(
            row['user_id'],
            "Booking Rejected",
            f"Booking #{booking_id} has been rejected. Please contact our support team for assistance.",
            'booking_rejected'
        )

            

        return jsonify({"message": "Booking rejected", "booking_id": booking_id}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/bookings/<int:booking_id>/trigger-refund', methods=['POST'])
def trigger_refund(booking_id):
    """Admin triggers a refund for a cancelled booking that was paid.
    Uses cancelled_at (or updated_at fallback) vs start_date to apply the 48h policy accurately."""
    try:
        import datetime as _dtm
        cur = get_cursor()
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ")
        commit_db()

        cur.execute("""
            SELECT status, payment_status, amount_paid, total_price,
                   start_date, cancelled_at, user_id
            FROM bookings WHERE id = %s
        """, (booking_id,))
        booking = cur.fetchone()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        if booking['status'] != 'Cancelled':
            return jsonify({"error": "Booking is not cancelled"}), 400
        if booking['payment_status'] in ['Refund Pending', 'Refunded']:
            return jsonify({"error": f"Booking already has payment_status: {booking['payment_status']}"}), 400

        amount_paid = float(booking.get('amount_paid') or booking.get('total_price') or 0)
        if amount_paid <= 0:
            return jsonify({"error": "No payment to refund"}), 400

        # Use cancelled_at if available, otherwise use NOW() as best estimate
        cancel_time = booking['cancelled_at']
        if cancel_time is None:
            cancel_dt = _dtm.datetime.now()
        elif isinstance(cancel_time, _dtm.datetime):
            cancel_dt = cancel_time.replace(tzinfo=None)
        else:
            cancel_dt = _dtm.datetime.fromisoformat(str(cancel_time)[:19])

        # Determine pickup datetime from start_date
        start_raw = booking['start_date']
        if isinstance(start_raw, (_dtm.date, _dtm.datetime)):
            pickup_dt = _dtm.datetime.combine(
                start_raw if isinstance(start_raw, _dtm.date) else start_raw.date(),
                _dtm.time(6, 0)
            )
        else:
            pickup_dt = _dtm.datetime.strptime(str(start_raw)[:10], '%Y-%m-%d').replace(hour=6)

        hours_before = (pickup_dt - cancel_dt).total_seconds() / 3600

        if hours_before >= 48:
            refund_amount = round(amount_paid, 2)
            non_refundable_fee = 0.0
            refund_note = f"Full refund - cancelled {hours_before:.1f}h before pickup (>= 48h)"
        else:
            non_refundable_fee = round(amount_paid * 0.20, 2)
            refund_amount = round(amount_paid - non_refundable_fee, 2)
            refund_note = (f"20% non-refundable: PHP {non_refundable_fee:.2f} - "
                           f"cancelled {hours_before:.1f}h before pickup (< 48h). "
                           f"Cancel: {cancel_dt.strftime('%Y-%m-%d %H:%M')} | "
                           f"Pickup: {pickup_dt.strftime('%Y-%m-%d %H:%M')}.")

        new_status = 'Refund Pending' if refund_amount > 0 else 'Cancelled'

        cur.execute("""
            UPDATE bookings SET payment_status = %s, refund_amount = %s, refund_note = %s
            WHERE id = %s
        """, (new_status, refund_amount, refund_note, booking_id))
        commit_db()

        try:
            notification_service.notify_user(
                booking['user_id'], "Refund Initiated",
                f"A refund of PHP {refund_amount:,.2f} has been initiated for Booking #{booking_id}. "
                "Please submit your refund account details.",
                'refund_initiated'
            )
        except Exception:
            pass

        return jsonify({
            "message": "Refund triggered successfully.",
            "refund_amount": refund_amount,
            "non_refundable_fee": non_refundable_fee,
            "refund_status": new_status,
            "hours_before_pickup": round(hours_before, 1),
            "cancellation_time": cancel_dt.strftime('%Y-%m-%d %H:%M'),
            "pickup_time": pickup_dt.strftime('%Y-%m-%d %H:%M')
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()


@app.route('/bookings/<int:booking_id>/refund-details', methods=['POST'])
def submit_refund_details(booking_id):
    """Customer submits their preferred refund channel and account details."""
    try:
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id')
        refund_channel = data.get('refund_channel', '').strip()
        refund_account_name = data.get('refund_account_name', '').strip()
        refund_account_number = data.get('refund_account_number', '').strip()
        refund_notes = data.get('refund_notes', '').strip()

        if not refund_channel or not refund_account_name or not refund_account_number:
            return jsonify({"error": "Refund channel, account name, and account number are required."}), 400

        cur = get_cursor()

        # Ensure columns exist
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_channel VARCHAR(50)")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_account_name VARCHAR(200)")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS refund_account_number VARCHAR(100)")
        commit_db()

        cur.execute("SELECT user_id, payment_status FROM bookings WHERE id = %s", (booking_id,))
        booking = cur.fetchone()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        if user_id and int(booking['user_id']) != int(user_id):
            return jsonify({"error": "Unauthorized"}), 403
        if booking['payment_status'] != 'Refund Pending':
            return jsonify({"error": "This booking is not pending a refund."}), 400

        note_parts = [f"Channel: {refund_channel}", f"Name: {refund_account_name}", f"Account: {refund_account_number}"]
        if refund_notes:
            note_parts.append(f"Notes: {refund_notes}")
        refund_detail_note = " | ".join(note_parts)

        cur.execute("""
            UPDATE bookings
            SET refund_channel = %s,
                refund_account_name = %s,
                refund_account_number = %s,
                refund_note = COALESCE(refund_note || ' | ', '') || %s
            WHERE id = %s
        """, (refund_channel, refund_account_name, refund_account_number, refund_detail_note, booking_id))
        commit_db()

        # Notify admins that customer submitted refund details
        try:
            _cur_rd = get_cursor()
            _cur_rd.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))
            _bk_rd = _cur_rd.fetchone()
            if _bk_rd:
                _uid_rd = _bk_rd['user_id']
                _cur_rd.execute("SELECT full_name FROM users WHERE id = %s", (_uid_rd,))
                _urow_rd = _cur_rd.fetchone()
                _uname_rd = _urow_rd['full_name'] if _urow_rd else f'User #{_uid_rd}'
                notification_service.notify_admins_inapp(
                    "Refund Details Submitted",
                    f"{_uname_rd} submitted refund details for Booking #{booking_id}. "
                    f"Channel: {refund_channel}, Account: {refund_account_name} ({refund_account_number}).",
                    'admin_refund_request',
                    type='admin_refund_request',
                    booking_id=booking_id
                )
        except Exception as _rd_err:
            print(f"Admin refund notification error: {_rd_err}")

        return jsonify({"message": "Refund details submitted successfully."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()


@app.route('/bookings/<int:booking_id>/cancel', methods=['PUT'])

def admin_cancel_booking(booking_id):

    """Cancel an approved/confirmed booking and trigger refund if needed."""

    try:

        cur = get_cursor()

        cur.execute("SELECT status, payment_status, vehicle_id, user_id, points_redeemed FROM bookings WHERE id=%s", (booking_id,))
        booking = cur.fetchone()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        # Determine if refund is needed
        new_payment_status = booking['payment_status']
        if booking['status'] in ['Approved', 'Confirmed'] or booking['payment_status'] == 'Paid':
            new_payment_status = 'Refund Pending'
        else:
            new_payment_status = 'Cancelled'

        cur.execute("""
            UPDATE bookings 
            SET status='Cancelled', payment_status=%s,
                cancelled_at = NOW() 
            WHERE id=%s
        """, (new_payment_status, booking_id))

        # Reset vehicle status to 'Available'
        if booking['vehicle_id']:
            cur.execute("UPDATE vehicles SET status='Available' WHERE id=%s", (booking['vehicle_id'],))

        # Refund redeemed loyalty points
        redeemed = int(booking.get('points_redeemed', 0) or 0)
        if redeemed > 0:
            cur.execute("UPDATE users SET loyalty_points = loyalty_points + %s WHERE id = %s", (redeemed, booking['user_id']))

        commit_db()



        reason = (request.json or {}).get('reason', 'No reason provided')

        # Insert notification using a fresh connection to avoid transaction conflicts
        notif_error = None
        try:
            import psycopg
            from config import SUPABASE_DB_URL
            from psycopg.rows import dict_row
            notif_conn = psycopg.connect(conninfo=SUPABASE_DB_URL)
            notif_cur = notif_conn.cursor(row_factory=dict_row)
            notif_cur.execute(
                "INSERT INTO notifications (user_id, admin_id, title, message, type) VALUES (%s, NULL, %s, %s, %s)",
                (
                    booking['user_id'],
                    "Booking Cancelled",
                    f"Your booking #{booking_id} has been cancelled by our team. Reason: {reason}. A refund will be initiated if applicable.",
                    'booking_cancelled_by_admin'
                )
            )
            notif_conn.commit()
            notif_cur.close()
            notif_conn.close()
        except Exception as notif_err:
            notif_error = str(notif_err)

        notification_service.notify_user(

            booking['user_id'],

            "Booking Cancelled",

            f"Your booking #{booking_id} has been cancelled by our team. Reason: {reason}. A refund will be initiated if applicable.",

            'booking_cancelled_by_admin'

        )



        return jsonify({"message": f"Booking #{booking_id} cancelled. Payment status: {new_payment_status}", "notif_debug": notif_error or "ok", "user_id_used": booking['user_id']}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/bookings/<int:booking_id>/pickup', methods=['PUT'])

def pickup_booking(booking_id):

    """Mark a booking as Picked Up."""

    try:

        cur = get_cursor()

        cur.execute("UPDATE bookings SET status='Picked Up' WHERE id=%s", (booking_id,))

        commit_db()

        

        cur.execute(
            """SELECT b.user_id, v.brand, v.model, b.end_date
               FROM bookings b
               JOIN vehicles v ON b.vehicle_id = v.id
               WHERE b.id = %s""",
            (booking_id,)
        )

        b_data = cur.fetchone()

        if b_data:
            notification_service.notify_user(
                b_data['user_id'],
                "Vehicle Picked Up",
                f"Drive safely! Booking #{booking_id} for {b_data['brand']} {b_data['model']} is now active. Return by {b_data['end_date']}.",
                'booking_picked_up'

            )

            

        # Log activity

        log_activity(

            admin_id=request.args.get('admin_id', 0),

            admin_name="Administrator",

            action='PICKUP_VEHICLE',

            target_type='BOOKING',

            target_id=str(booking_id),

            details=f"Marked booking #{booking_id} as Picked Up"

        )

            

        return jsonify({"message": "Vehicle marked as Picked Up", "booking_id": booking_id}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/bookings/<int:booking_id>/complete', methods=['PUT'])

def complete_booking(booking_id):

    """Mark a booking as Completed/Returned."""

    try:

        cur = get_cursor()

        cur.execute("SELECT user_id, points_earned, status FROM bookings WHERE id=%s", (booking_id,))
        b_info = cur.fetchone()
        
        if not b_info:
            return jsonify({"error": "Booking not found"}), 404
            
        # Only award points if it was not already Completed
        if b_info['status'] != 'Completed':
            cur.execute("UPDATE bookings SET status='Completed' WHERE id=%s", (booking_id,))
            
            # Reset vehicle status to 'Available'
            cur.execute("UPDATE vehicles SET status='Available' WHERE id=(SELECT vehicle_id FROM bookings WHERE id=%s)", (booking_id,))
            
            # Award points
            earned = int(b_info.get('points_earned', 0) or 0)
            if earned > 0:
                cur.execute("UPDATE users SET loyalty_points = loyalty_points + %s WHERE id = %s", (earned, b_info['user_id']))
                
            commit_db()

        

        cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))
        b_data = cur.fetchone()
        if b_data:
            notification_service.notify_user(
                b_data['user_id'],
                "Booking Completed",
                f"Thank you for choosing Autoride! Booking #{booking_id} is now completed. We hope to see you again.",
                'booking_completed'

            )

            

        # Log activity

        log_activity(

            admin_id=request.args.get('admin_id', 0),

            admin_name="Administrator",

            action='COMPLETE_RENTAL',

            target_type='BOOKING',

            target_id=str(booking_id),

            details=f"Marked booking #{booking_id} as Completed/Returned"

        )

            

        return jsonify({"message": "Vehicle marked as Returned", "booking_id": booking_id}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/settings/driver_wage', methods=['GET', 'PUT'])

def handle_driver_wage():

    try:

        cur = get_cursor()

        if request.method == 'GET':

            cur.execute("SELECT value FROM system_settings WHERE key='driver_wage'")

            row = cur.fetchone()

            wage = row['value'] if row else '500'

            return jsonify({'wage': wage}), 200

            

        elif request.method == 'PUT':

            data = request.json

            wage = str(data.get('wage', '500'))

            cur.execute("""

                INSERT INTO system_settings (key, value) VALUES ('driver_wage', %s)

                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value

            """, (wage,))

            commit_db()

            return jsonify({'message': 'Wage updated', 'wage': wage}), 200

            

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



# ==================== ADMIN DRIVER APPROVAL ====================



@app.route('/drivers', methods=['GET'])

def get_all_drivers():

    """Get all driver applications for admin panel."""

    try:

        cur = get_cursor()

        cur.execute("""

            SELECT id, user_id, full_name, license_number, contact_info, status, rejection_reason, license_document

            FROM drivers

            ORDER BY id DESC

        """)

        data = cur.fetchall()

        drivers = [dict(row) for row in data]

        return jsonify(drivers), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/drivers/<int:driver_id>/approve', methods=['PUT', 'POST'])

def approve_driver(driver_id):

    """Approve a pending driver application."""

    try:

        cur = get_cursor()

        cur.execute("SELECT status FROM drivers WHERE id=%s", (driver_id,))

        row = cur.fetchone()

        if not row:

            return jsonify({"error": "Driver not found"}), 404

        if row['status'] != 'Pending':

            return jsonify({"error": f"Cannot approve a driver with status '{row['status']}'"}), 400



        cur.execute("UPDATE drivers SET status='Approved' WHERE id=%s", (driver_id,))

        commit_db()

        

        # Send SMS notification

        cur.execute(

            """SELECT d.user_id, u.full_name

               FROM drivers d

               JOIN users u ON d.user_id = u.id

               WHERE d.id = %s""",

            (driver_id,)

        )

        d_data = cur.fetchone()

        if d_data:
            notification_service.notify_user(
                d_data['user_id'],
                "Driver Application Approved",
                f"Congratulations, {d_data['full_name']}! Your driver application has been approved. You can now start accepting bookings.",
                'driver_approved'

            )

            

        return jsonify({"message": "Driver approved", "driver_id": driver_id}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/drivers/<int:driver_id>/reject', methods=['PUT', 'POST'])

def reject_driver(driver_id):

    """Reject a pending driver application."""

    data = request.json or {}

    reason = data.get('reason', '')

    try:

        cur = get_cursor()

        cur.execute("SELECT status FROM drivers WHERE id=%s", (driver_id,))

        row = cur.fetchone()

        if not row:

            return jsonify({"error": "Driver not found"}), 404

        if row['status'] != 'Pending':

            return jsonify({"error": f"Cannot reject a driver with status '{row['status']}'"}), 400



        cur.execute("UPDATE drivers SET status='Rejected', rejection_reason=%s WHERE id=%s", (reason, driver_id))

        commit_db()

        

        # Send SMS notification

        cur.execute("SELECT user_id FROM drivers WHERE id = %s", (driver_id,))

        d_data = cur.fetchone()

        if d_data:
            notification_service.notify_user(
                d_data['user_id'],
                "Driver Application Rejected",
                f"Your driver application was not approved. Reason: {reason}. You may re-apply once the issues are resolved.",
                'driver_rejected'

            )

            

        return jsonify({"message": "Driver rejected", "driver_id": driver_id}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



# ==================== DRIVER PORTAL API ====================



@app.route('/driver/apply', methods=['POST'])

def apply_driver():

    # Ensure license_document column exists (safe migration)

    try:

        cur = get_cursor()

        cur.execute("ALTER TABLE drivers ADD COLUMN IF NOT EXISTS license_document VARCHAR(255)")

        cur.execute("ALTER TABLE drivers ADD COLUMN IF NOT EXISTS user_id INT")

        commit_db()

        cur.close()

    except Exception:

        pass



    user_id = request.form.get('user_id')

    full_name = request.form.get('full_name')

    license_number = request.form.get('license_number')

    contact_info = request.form.get('contact_info')



    if not all([user_id, full_name, license_number, contact_info]):

        return jsonify({"error": "Missing application details"}), 400



    if 'license_document' not in request.files or request.files['license_document'].filename == '':

        return jsonify({"error": "Driver's license document is required"}), 400



    try:

        cur = get_cursor()



        # Check if already applied

        cur.execute("SELECT id FROM drivers WHERE user_id=%s", (user_id,))

        if cur.fetchone():

            return jsonify({"error": "Application already submitted for this user."}), 400



        # Save license document

        file = request.files['license_document']

        ext = os.path.splitext(secure_filename(file.filename))[1]

        filename = secure_filename(f"license_doc_{user_id}{ext}")

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        file.save(filepath)



        cur.execute("""

            INSERT INTO drivers (user_id, full_name, license_number, contact_info, license_document, status)

            VALUES (%s, %s, %s, %s, %s, 'Pending')

        """, (user_id, full_name, license_number, contact_info, filename))

        commit_db()

        return jsonify({"message": "Application submitted"}), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()





@app.route('/driver/status', methods=['GET'])

def driver_status():

    user_id = request.args.get('user_id')

    if not user_id:

        return jsonify({"error": "user_id required"}), 400

        

    try:

        cur = get_cursor()

        cur.execute("SELECT id, status, rejection_reason FROM drivers WHERE user_id=%s ORDER BY id DESC LIMIT 1", (user_id,))

        row = cur.fetchone()

        if not row:

            return jsonify({"status": "Not Applied"}), 200

        return jsonify(dict(row)), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/driver/bookings', methods=['GET'])

def get_driver_bookings():

    user_id = request.args.get('user_id')

    if not user_id:

        return jsonify({"error": "user_id required"}), 400

        

    try:

        cur = get_cursor()

        # Ensure user is an approved driver

        cur.execute("SELECT id FROM drivers WHERE user_id=%s AND status='Approved'", (user_id,))

        driver = cur.fetchone()

        if not driver:

            return jsonify({"error": "Driver not found or not approved"}), 403

            

        driver_id = driver['id']

        

        cur.execute("""

            SELECT b.id, b.start_date, b.end_date, b.pickup_location, b.status,

                   u.full_name AS client_name, u.phone AS client_phone,

                   v.brand, v.model, v.plate_number

            FROM bookings b

            JOIN users u ON b.user_id = u.id

            JOIN vehicles v ON b.vehicle_id = v.id

            WHERE b.driver_id = %s

            ORDER BY b.start_date DESC

        """, (driver_id,))

        rows = cur.fetchall()

        return jsonify([dict(r) for r in rows]), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/driver/bookings/<int:booking_id>/status', methods=['PUT'])

def update_driver_booking_status(booking_id):

    data = request.json

    user_id = data.get('user_id')

    new_status = data.get('status')

    

    if not user_id or not new_status:

        return jsonify({"error": "user_id and status required"}), 400

        

    try:

        cur = get_cursor()

        # Ensure user is an approved driver

        cur.execute("SELECT id FROM drivers WHERE user_id=%s AND status='Approved'", (user_id,))

        driver = cur.fetchone()

        if not driver:

            return jsonify({"error": "Driver not found or not approved"}), 403

            

        driver_id = driver['id']

        

        # Verify driver is assigned to this booking

        cur.execute("SELECT id FROM bookings WHERE id=%s AND driver_id=%s", (booking_id, driver_id))

        booking = cur.fetchone()

        if not booking:

            return jsonify({"error": "Booking not found or not assigned to this driver"}), 403

            

        cur.execute("UPDATE bookings SET status=%s WHERE id=%s", (new_status, booking_id))

        commit_db()

        return jsonify({"message": "Booking status updated"}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



# ==================== ADMIN REPORTS & ANALYTICS ====================





@app.route('/admin/download-report', methods=['POST'])
def download_report():
    try:
        content = request.form.get('content', '')
        filename = request.form.get('filename', 'report.csv')
        mimetype = request.form.get('mimetype', 'text/csv')
        
        response = make_response(content)
        response.headers['Content-Type'] = f"{mimetype}; charset=utf-8"
        if mimetype == 'text/csv':
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        else:
            response.headers['Content-Disposition'] = 'inline'
            
        return response
    except Exception as e:
        print(f"Error in download_report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/detailed-stats', methods=['GET'])

def get_detailed_stats():
    """Aggregated stats for the executive dashboard charts."""
    admin_id = request.args.get('admin_id')
    chart_type = request.args.get('type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status_filter = request.args.get('status')
    vehicle_type = request.args.get('vehicle_type')

    try:
        cur = get_cursor()
        
        # Determine location filter
        location_filter = None
        if admin_id:
            cur.execute("SELECT role, assigned_location FROM users WHERE id = %s", (admin_id,))
            adm = cur.fetchone()
            if adm and adm['role'] == 'admin' and adm['assigned_location']:
                location_filter = adm['assigned_location']

        def apply_filters(query, params, prefix_b='b', prefix_v='v', skip_status=False):
            if location_filter:
                query += f" AND {prefix_v}.location = %s"
                params.append(location_filter)
            if date_from:
                query += f" AND {prefix_b}.start_date >= %s"
                params.append(date_from)
            if date_to:
                query += f" AND {prefix_b}.start_date <= %s"
                params.append(date_to)
            if not skip_status and status_filter and status_filter != 'all':
                query += f" AND {prefix_b}.status = %s"
                params.append(status_filter)
            if vehicle_type and vehicle_type != 'all':
                query += f" AND {prefix_v}.type = %s"
                params.append(vehicle_type)
            return query, params

        # 1. Revenue & Bookings
        rev_query = """
            SELECT 
                SUM(CASE WHEN b.status = 'Cancelled' THEN (COALESCE(b.amount_paid, 0) - COALESCE(b.refund_amount, 0)) ELSE b.total_price END) as total_revenue,
                COUNT(b.id) as total_bookings
            FROM bookings b 
            JOIN vehicles v ON b.vehicle_id = v.id 
            WHERE (b.status != 'Cancelled' OR (b.status = 'Cancelled' AND COALESCE(b.amount_paid, 0) > COALESCE(b.refund_amount, 0)))
        """
        rev_params = []
        rev_query, rev_params = apply_filters(rev_query, rev_params, 'b', 'v', skip_status=False)
        cur.execute(rev_query, tuple(rev_params))
        basic_stats = cur.fetchone()
        
        # 2. Daily Revenue (Last 30 days)
        trend_query = """
            SELECT 
                TO_CHAR(b.start_date, 'YYYY-MM-DD') as day,
                SUM(CASE WHEN b.status = 'Cancelled' THEN (COALESCE(b.amount_paid, 0) - COALESCE(b.refund_amount, 0)) ELSE b.total_price END) as amount,
                COUNT(b.id) as booking_count
            FROM bookings b
            JOIN vehicles v ON b.vehicle_id = v.id
            WHERE b.start_date >= CURRENT_DATE - INTERVAL '30 days' 
              AND (b.status != 'Cancelled' OR (b.status = 'Cancelled' AND COALESCE(b.amount_paid, 0) > COALESCE(b.refund_amount, 0)))
        """
        trend_params = []
        trend_query, trend_params = apply_filters(trend_query, trend_params, 'b', 'v', skip_status=False)
        trend_query += " GROUP BY day ORDER BY day ASC"
        cur.execute(trend_query, tuple(trend_params))
        revenue_trend = cur.fetchall()
        
        # 3. Fleet Distribution
        # For fleet, we don't have bookings 'b', just 'v'
        fleet_query = "SELECT status, COUNT(*) as count FROM vehicles v WHERE 1=1"
        fleet_params = []
        if location_filter:
            fleet_query += " AND v.location = %s"
            fleet_params.append(location_filter)
        if vehicle_type and vehicle_type != 'all':
            fleet_query += " AND v.type = %s"
            fleet_params.append(vehicle_type)
        fleet_query += " GROUP BY status"
        cur.execute(fleet_query, tuple(fleet_params))
        fleet_dist = cur.fetchall()
        
        # 4. Top Performing Vehicles
        top_query = """
            SELECT v.brand, v.model, v.plate_number, COUNT(b.id) as booking_count, 
                   COALESCE(SUM(CASE WHEN b.status = 'Cancelled' THEN (COALESCE(b.amount_paid, 0) - COALESCE(b.refund_amount, 0)) ELSE b.total_price END), 0) as revenue
            FROM vehicles v
            JOIN bookings b ON v.id = b.vehicle_id
            WHERE (b.status != 'Cancelled' OR (b.status = 'Cancelled' AND COALESCE(b.amount_paid, 0) > COALESCE(b.refund_amount, 0)))
        """
        top_params = []
        top_query, top_params = apply_filters(top_query, top_params, 'b', 'v', skip_status=False)
        top_query += " GROUP BY v.id, v.brand, v.model, v.plate_number ORDER BY revenue DESC LIMIT 5"
        cur.execute(top_query, tuple(top_params))
        top_vehicles = [{"brand": r.get('brand'), "model": r.get('model'), "plate_number": r.get('plate_number'), "booking_count": int(r.get('booking_count') or 0), "revenue": float(r.get('revenue') or 0)} for r in cur.fetchall()]

        # 5. Expenses calculation
        exp_query = "SELECT COALESCE(SUM(e.amount), 0) as total_expenses FROM vehicle_expenses e JOIN vehicles v ON e.vehicle_id = v.id WHERE 1=1"
        exp_params = []
        if location_filter:
            exp_query += " AND v.location = %s"
            exp_params.append(location_filter)
        if date_from:
            exp_query += " AND e.expense_date >= %s"
            exp_params.append(date_from)
        if date_to:
            exp_query += " AND e.expense_date <= %s"
            exp_params.append(date_to)
        if vehicle_type and vehicle_type != 'all':
            exp_query += " AND v.type = %s"
            exp_params.append(vehicle_type)
        cur.execute(exp_query, tuple(exp_params))
        total_expenses = float(cur.fetchone()['total_expenses'] or 0)

        total_revenue = float(basic_stats['total_revenue'] or 0)
        net_profit = total_revenue - total_expenses

        return jsonify({
            "totalRevenue": total_revenue,
            "totalBookings": basic_stats['total_bookings'] or 0,
            "revenueTrend": revenue_trend,
            "fleetDistribution": fleet_dist,
            "topVehicles": top_vehicles,
            "totalExpenses": total_expenses,
            "netProfit": net_profit
        })

    except Exception as e:
        print(f"Error in detailed stats: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/bookings/<int:booking_id>/receipt', methods=['GET'])

def download_receipt(booking_id):

    """Generate and download a PDF receipt for a booking."""

    try:

        cur = get_cursor()

        

        # 1. Fetch Booking

        cur.execute("SELECT * FROM bookings WHERE id = %s", (booking_id,))

        booking = cur.fetchone()

        if not booking:

            return jsonify({"error": "Booking not found"}), 404

            

        booking_dict = dict(booking)

        

        # 2. Fetch User

        cur.execute("SELECT full_name, email FROM users WHERE id = %s", (booking_dict['user_id'],))

        user = cur.fetchone()

        user_dict = dict(user) if user else {"full_name": "Valued Customer", "email": "N/A"}

        

        # 3. Fetch Vehicle

        cur.execute("SELECT brand, model, plate_number FROM vehicles WHERE id = %s", (booking_dict['vehicle_id'],))

        vehicle = cur.fetchone()

        vehicle_dict = dict(vehicle) if vehicle else {"brand": "Unknown", "model": "Vehicle", "plate_number": "N/A"}

        

        # 4. Generate PDF

        pdf_content = generate_booking_pdf(booking_dict, user_dict, vehicle_dict)

        

        return send_file(

            io.BytesIO(pdf_content),

            mimetype='application/pdf',

            as_attachment=False,

            download_name=f'Autoride_Receipt_{booking_id}.pdf'

        )

        

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/reports/top-vehicles', methods=['GET'])

def report_top_vehicles():

    """Top 5 most-rented vehicles with booking count and total revenue."""

    admin_id = request.args.get('admin_id')

    try:

        cur = get_cursor()

        

        # Determine location filter

        location_filter = None

        if admin_id:

            cur.execute("SELECT role, assigned_location FROM users WHERE id = %s", (admin_id,))

            adm = cur.fetchone()

            if adm and adm['role'] == 'admin' and adm['assigned_location']:

                location_filter = adm['assigned_location']



        query = """

            SELECT CONCAT(v.brand, ' ', v.model) AS vehicle_name,

                   COUNT(b.id) AS total_bookings,

                   COALESCE(SUM(b.total_price), 0) AS total_revenue

            FROM bookings b

            JOIN vehicles v ON b.vehicle_id = v.id

        """

        params = []

        if location_filter:

            query += " WHERE v.location = %s "

            params.append(location_filter)

            

        query += """

            GROUP BY v.id, v.brand, v.model

            ORDER BY total_bookings DESC

            LIMIT 5

        """

        

        cur.execute(query, tuple(params))

        rows = cur.fetchall()

        vehicles = []

        for r in rows:

            d = dict(r)

            d['total_revenue'] = float(d['total_revenue'])

            vehicles.append(d)



        return jsonify({"vehicles": vehicles}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()





@app.route('/support', methods=['POST'])

def submit_support():

    data = request.json

    name = data.get('name')

    email = data.get('email', '') 

    subject = data.get('subject')

    message = data.get('message')

    

    if not all([name, subject, message]):

        return jsonify({"error": "Missing required support fields"}), 400

        

    try:

        cur = get_cursor()

        cur.execute("""

            INSERT INTO contact_queries (name, email, subject, message, status, is_read)

            VALUES (%s, %s, %s, %s, 'pending', FALSE)

        """, (name, email, subject, message))

        commit_db()

        return jsonify({"message": "Support ticket submitted successfully."}), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/admin/support', methods=['GET'])

def get_all_support_tickets():

    try:

        cur = get_cursor()

        cur.execute("SELECT * FROM contact_queries ORDER BY created_at DESC")

        tickets = cur.fetchall()

        result = [dict(t) for t in tickets]

        return jsonify(result), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/admin/support/<int:ticket_id>', methods=['PUT'])

def resolve_support_ticket(ticket_id):

    data = request.json

    reply = data.get('admin_reply', '')

    status = data.get('status', 'resolved')

    

    try:

        cur = get_cursor()

        cur.execute("""

            UPDATE contact_queries 

            SET admin_reply = %s, status = %s, is_read = TRUE, updated_at = CURRENT_TIMESTAMP

            WHERE id = %s

        """, (reply, status, ticket_id))

        commit_db()

        return jsonify({"message": "Ticket resolved successfully."}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/admin/instructions', methods=['GET', 'POST'])

def manage_instructions():

    try:

        cur = get_cursor()

        if request.method == 'POST':

            data = request.json

            instruction = data.get('instruction')

            

            if instruction:

                cur.execute("INSERT INTO pickup_instructions (icon, title, description) VALUES ('check', 'Requirement', %s)", (instruction,))

                commit_db()

                return jsonify({"message": "Instruction added"}), 201

            return jsonify({"error": "instruction text required"}), 400

        else:

            cur.execute("SELECT description as instruction_text, TRUE as is_active FROM pickup_instructions ORDER BY id DESC")

            instructions = cur.fetchall()

            return jsonify([dict(i) for i in instructions]), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/newsletter', methods=['POST'])

def subscribe_newsletter():

    data = request.json

    email = data.get('email')

    if not email:

        return jsonify({"error": "Email required"}), 400

    

    try:

        cur = get_cursor()

        cur.execute("INSERT INTO subscribers (email, status) VALUES (%s, 'active') ON CONFLICT(email) DO NOTHING", (email,))

        commit_db()

        return jsonify({"message": "Subscribed successfully"}), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()







# --- Admin Verification Endpoints ---



@app.route('/admin/pending-verifications', methods=['GET'])

def get_pending_verifications():

    try:

        cur = get_cursor()

        # Ensure license detail columns exist
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS license_number VARCHAR(50)")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS license_expiry DATE")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS license_type VARCHAR(50)")
        commit_db()

        # is_verified = 1 means pending review
        cur.execute("""
            SELECT id, full_name, email, phone,
                   license_image_url AS license_image,
                   license_number, license_expiry, license_type,
                   is_verified
            FROM users
            WHERE license_image_url IS NOT NULL AND is_verified = 1
            ORDER BY id DESC
        """)

        users = cur.fetchall()

        result = []
        for u in users:
            d = dict(u)
            if d.get('license_expiry'):
                d['license_expiry'] = str(d['license_expiry'])
            result.append(d)

        return jsonify(result), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/admin/verify-user', methods=['POST'])

def verify_user():

    data = request.json or {}

    user_id = data.get('user_id')

    status = data.get('status') # 1 for Approve, 2 for Reject

    

    if not user_id or status is None:

        return jsonify({"error": "user_id and status are required"}), 400

        

    try:

        cur = get_cursor()

        cur.execute("UPDATE users SET is_verified = %s WHERE id = %s", (status, user_id))

        commit_db()

        return jsonify({"message": f"User status updated to {status}"}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



# ==================== CHATBOT API ====================

import re as _re



CHATBOT_FAQ = [

    {

        "keywords": ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "kumusta", "musta"],

        "response": "Hello!  Welcome to Autoride! I'm your virtual assistant. I can help you with:\n\n- Booking a vehicle\n- Pricing & rates\n- Requirements & documents\n- Cancellation policy\n- Payment methods\n- Driver services\n\nWhat would you like to know?"

    },

    {

        "keywords": ["how to book", "booking", "rent", "reserve", "paano mag book", "pano mag rent", "how to rent"],

        "response": " **How to Book a Vehicle:**\n\n1. Browse our vehicle catalog on the homepage\n2. Click on the vehicle you want\n3. Select your rental dates (start & end)\n4. Choose pickup & return locations\n5. Select add-ons (driver, insurance, etc.)\n6. Review the total and proceed to checkout\n7. Complete payment to confirm your booking!\n\nNeed help with a specific step?"

    },

    {

        "keywords": ["price", "rate", "cost", "how much", "magkano", "presyo", "fee", "pricing", "daily rate"],

        "response": " **Pricing Information:**\n\nOur rates vary by vehicle type:\n- **Cars**  Starting at PHP1,500/day\n- **SUVs**  Starting at PHP2,500/day\n- **Vans**  Starting at PHP3,000/day\n- **Trucks**  Starting at PHP3,500/day\n\nRates include basic insurance. Add-ons like a professional driver (+PHP500/day) are available.\n\nYou can see exact pricing on each vehicle's detail page!"

    },

    {

        "keywords": ["requirement", "document", "need to bring", "valid id", "license", "ano kailangan", "requirements"],

        "response": " **Requirements for Renting:**\n\n1. **Valid Government ID** (Driver's License, Passport, or National ID)\n2. **Proof of Address** (Utility bill or bank statement)\n3. **Valid Driver's License** (if self-drive)\n4. **Security Deposit** (varies per vehicle)\n5. Must be **21 years or older**\n\nFor corporate rentals, additional documents may be needed. Contact support for details!"

    },

    {

        "keywords": ["cancel", "cancellation", "refund", "change booking", "reschedule", "cancel booking", "pano mag cancel"],

        "response": " **Cancellation & Refund Policy:**\n\n- **Free cancellation** if done 48+ hours before pickup\n- **50% refund** if cancelled 24-48 hours before\n- **No refund** if cancelled less than 24 hours before\n- **Rescheduling** is free if done 24+ hours before\n\nTo cancel or reschedule, go to your Dashboard -> My Bookings -> select the booking -> Cancel/Reschedule."

    },

    {

        "keywords": ["payment", "pay", "gcash", "maya", "credit card", "bayad", "paano magbayad", "payment method"],

        "response": " **Payment Methods:**\n\nWe accept the following:\n- **Credit/Debit Cards** (Visa, Mastercard)\n- **GCash**\n- **Maya (PayMaya)**\n- **Bank Transfer**\n- **Cash** (at pickup location)\n\nPayment is required to confirm your booking. You'll receive a receipt via email."

    },

    {

        "keywords": ["driver", "chauffeur", "may driver", "with driver", "hire driver", "professional driver"],

        "response": " **Driver Services:**\n\nYes! We offer professional drivers as an add-on:\n\n- **Cost:** Additional PHP500/day\n- **Licensed & verified** professional drivers\n- **Available for all vehicle types**\n- Select the 'With Driver' option during booking\n\nOur drivers are thoroughly vetted, licensed, and experienced. Perfect for long trips or if you prefer not to drive!"

    },

    {

        "keywords": ["insurance", "coverage", "accident", "damage", "protection"],

        "response": " **Insurance & Coverage:**\n\n- **Basic Insurance**  Included free with every rental\n- **Premium Insurance**  Available as add-on for comprehensive coverage\n- Covers collision damage, theft, and third-party liability\n- Deductible may apply for certain claims\n\nWe recommend premium insurance for peace of mind on longer trips!"

    },

    {

        "keywords": ["pickup", "location", "where", "saan", "branch", "drop off", "return", "delivery"],

        "response": " **Pickup & Return Locations:**\n\nYou set your preferred pickup and return locations during booking:\n- Enter your **Province, Municipality, and Barangay**\n- Separate pickup and return locations are supported\n- Delivery to your location may be available\n\nExact availability depends on vehicles in your area."

    },

    {

        "keywords": ["register", "sign up", "create account", "gawa account", "account"],

        "response": " **Creating an Account:**\n\n1. Click **Register** on the top right\n2. Enter your full name, email, and password\n3. Verify your email address\n4. Complete your profile with contact info\n5. You're ready to book!\n\nYou can also sign in with Google for faster access."

    },

    {

        "keywords": ["tutorial", "guide", "how to use", "how to book", "paano gamitin", "paano mag-book", "step by step", "how does it work", "get started", "beginners", "new user", "first time"],

        "response": " **How to Use Autoride \u2014 Step-by-Step Guide:**\n\n**Step 1: Create an Account**\n\u2022 Register with your Name, Gmail, and Password\n\u2022 Verify your email with the 6-digit code sent to you\n\u2022 Or use **Sign in with Google** for instant access\n\n**Step 2: Complete Your Profile**\n\u2022 Go to **Profile** and fill in your contact info\n\u2022 Upload your **Driver's License** (front and back photo)\n\u2022 Add emergency contact details\n\u2022 Wait for verification approval\n\n**Step 3: Browse Vehicles**\n\u2022 Go to **Browse Cars** or the Vehicles page\n\u2022 Filter by type: Sedan, SUV, Van, Pickup\n\u2022 Search by name or location\n\u2022 Tap any car to see details, photos, specs, and pricing\n\n**Step 4: Book a Vehicle**\n\u2022 Select your **start and end dates**\n\u2022 Choose pickup and dropoff location\n\u2022 Review your booking summary\n\u2022 Click **Confirm Booking**\n\n**Step 5: Pay for Your Booking**\n\u2022 Choose: GCash, Maya, Credit Card, Bank Transfer, or Cash\n\u2022 Complete payment instructions\n\u2022 You will receive a **booking confirmation email**\n\n**Step 6: Manage Your Booking**\n\u2022 Track your booking in the **My Bookings** tab\n\u2022 View booking status in real-time\n\u2022 Cancel or request support if needed\n\n Need help? Use **Live Chat** or check our **Support** page!"

    },

    {

        "keywords": ["forgot password", "reset password", "can't login", "hindi makapasok", "password reset"],

        "response": " **Password Reset:**\n\nIf you forgot your password:\n1. Go to the Login page\n2. Click 'Forgot Password'\n3. Enter your registered email\n4. Check your inbox for the reset link\n5. Set a new password\n\nStill can't access your account? Submit a support ticket and we'll help!"

    },

    {

        "keywords": ["contact", "phone", "email", "support", "help", "customer service", "tulong"],

        "response": " **Contact Us:**\n\n- **Support Page:** Visit our Support page to submit a ticket\n- **Response Time:** Within 24 hours\n- **Live Chat:** You're using it right now! \n\nFor urgent concerns, submit a support ticket with subject 'URGENT' and we'll prioritize your request."

    },

    {

        "keywords": ["promo", "coupon", "discount", "code", "voucher", "sale"],

        "response": " **Promos & Discounts:**\n\nWe regularly offer promotional codes! Here's how to use one:\n1. Select your vehicle and set your dates\n2. In the booking form, find the **Promo Code** field\n3. Enter your code and click **Apply**\n4. The discount will be reflected in your total\n\nFollow us on social media for the latest promos!"

    },

    {

        "keywords": ["fuel", "gas", "gasoline", "diesel", "petrol", "fuel policy"],

        "response": " **Fuel Policy:**\n\n- Vehicles are provided with a **full tank**\n- Please return the vehicle with a **full tank**\n- If returned with less fuel, a refueling charge applies\n- Fuel type is listed on each vehicle's detail page (Petrol, Diesel, Hybrid, Electric)"

    },

    {

        "keywords": ["age", "minimum age", "how old", "edad", "age limit"],

        "response": " **Age Requirements:**\n\n- Minimum age: **21 years old**\n- Must have a valid driver's license (for self-drive)\n- Drivers under 25 may be subject to a young driver surcharge\n- No maximum age limit (valid license required)"

    },

    {

        "keywords": ["thank", "thanks", "salamat", "ok", "okay", "got it", "sige"],

        "response": "You're welcome!  Happy to help. If you have any more questions, just type away. Enjoy your ride with Autoride! "

    },

    {

        "keywords": ["apply driver", "become driver", "mag apply", "driver application"],

        "response": " **Apply as a Driver:**\n\n1. Click **Apply as Driver** on the homepage\n2. Fill in your full name, license number, and contact info\n3. Upload your driver's license document\n4. Submit your application\n5. Wait for admin approval (usually within 24-48 hours)\n\nOnce approved, you'll be able to accept driving assignments!"

    },

    {

        "keywords": ["status", "booking status", "where is", "track", "update"],

        "response": " **Check Your Booking Status:**\n\n1. Log in to your account\n2. Go to **Dashboard** (click your profile or the Dashboard link)\n3. Find your booking under **My Bookings**\n4. Status will show: Pending, Confirmed, Active, or Completed\n\nYou'll also receive email notifications for status changes!"

    }

]



def match_chatbot_intent(message):

    """Match user message against FAQ knowledge base using keyword scoring"""

    msg_lower = message.lower().strip()

    

    best_match = None

    best_score = 0

    

    for faq in CHATBOT_FAQ:

        score = 0

        for keyword in faq["keywords"]:

            if keyword in msg_lower:

                # Longer keyword matches are worth more

                score += len(keyword.split())

        

        if score > best_score:

            best_score = score

            best_match = faq

    

    if best_match and best_score > 0:

        return best_match["response"]

    

    # Default fallback

    return ("I'm not sure I understand that question. \n\nHere are some things I can help with:\n"

            "- **Booking**  How to rent a vehicle\n"

            "- **Pricing**  Rates and costs\n"

            "- **Requirements**  Documents needed\n"

            "- **Cancellation**  Refund policy\n"

            "- **Payment**  Payment methods\n"

            "- **Driver**  Hire a professional driver\n\n"

            "Or you can visit our **Support** page to submit a ticket for personalized assistance!")





@app.route('/chat', methods=['POST'])

def chat_endpoint():

    """Smart FAQ chatbot endpoint"""

    data = request.json

    message = data.get('message', '').strip()

    user_id = data.get('user_id', None)

    

    if not message:

        return jsonify({"error": "Message is required"}), 400

    

    # Get bot response

    bot_response = match_chatbot_intent(message)

    

    # Store chat messages in database (optional, graceful fail)

    try:

        cur = get_cursor()

        cur.execute("""

            INSERT INTO chat_messages (user_id, user_message, bot_response, created_at)

            VALUES (%s, %s, %s, NOW())

        """, (user_id, message, bot_response))

        commit_db()

        cur.close()

    except Exception as e:

        # Don't fail the response if logging fails (table might not exist yet)

        print(f"Chat log save skipped: {e}")

    

    return jsonify({

        "response": bot_response,

        "matched": bot_response != match_chatbot_intent("xyznonexistent")  # whether it matched an intent

    })







@app.route('/admin/login', methods=['POST'], strict_slashes=False)

def admin_login():
    data = request.get_json(force=True, silent=True)

    if not data:
        return jsonify({"error": "No data received - check Content-Type"}), 400

    email = data.get('email')

    password = data.get('password')

    

    try:

        cur = get_cursor()

        # Only allow is_verified = 1 (Active)

        cur.execute("SELECT id, full_name, role, assigned_location, password FROM users WHERE email=%s AND role IN ('admin', 'super_admin')", (email,))
        admin_row = cur.fetchone()
        user = None
        if admin_row:
            stored = admin_row['password'] or ''
            try:
                pw_ok = bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8'))
            except Exception:
                pw_ok = (stored == password)
                if pw_ok:
                    new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    cur.execute("UPDATE users SET password=%s WHERE id=%s", (new_hash, admin_row['id']))
                    commit_db()
            if pw_ok:
                user = admin_row

        

        if user:

            # Log activity

            log_activity(

                admin_id=user['id'],

                admin_name=user['full_name'],

                action='ADMIN_LOGIN',

                target_type='AUTH',

                details=f"Admin logged in from {request.remote_addr}"

            )



            return jsonify({

                "id": user['id'],

                "full_name": user['full_name'],

                "role": user['role'],

                "assigned_location": user['assigned_location']

            }), 200

        else:

            return jsonify({"error": "Invalid admin credentials or account disabled"}), 401

    except Exception as e:
        import traceback as _tb
        _err = _tb.format_exc()
        print(f'ERROR in admin_login: {_err}')
        return jsonify({'error': str(e), 'detail': _err[-800:]}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/admin/list', methods=['GET'])

def list_admins():

    requester_id = request.args.get('requester_id')

    try:

        cur = get_cursor()

        cur.execute("SELECT role FROM users WHERE id=%s", (requester_id,))

        requester = cur.fetchone()

        if not requester or requester['role'] != 'super_admin':

            return jsonify({"error": "Unauthorized"}), 403



        cur.execute("SELECT id, full_name, email, role, is_verified, assigned_location FROM users WHERE role IN ('admin', 'super_admin') ORDER BY id DESC")

        admins = cur.fetchall()

        return jsonify(admins), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 400

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/admin/update/<int:user_id>', methods=['PUT'])

def update_admin(user_id):

    data = request.json

    requester_id = data.get('requester_id')

    name = data.get('name')

    email = data.get('email')

    password = data.get('password')

    role = data.get('role')

    assigned_location = data.get('assigned_location')



    try:

        cur = get_cursor()

        cur.execute("SELECT full_name, role FROM users WHERE id=%s", (requester_id,))

        requester = cur.fetchone()

        if not requester or requester['role'] != 'super_admin':

            return jsonify({"error": "Unauthorized"}), 403



        # Prevent editing super_admin accounts
        cur.execute("SELECT role FROM users WHERE id=%s", (user_id,))
        target = cur.fetchone()
        if target and target['role'] == 'super_admin':
            return jsonify({"error": "Super Admin accounts cannot be modified."}), 403


        # Split name into first/last for generated full_name column
        _admin_name_parts = (name or '').strip().split(' ', 1)
        _admin_first = _admin_name_parts[0] if _admin_name_parts else name
        _admin_last = _admin_name_parts[1] if len(_admin_name_parts) > 1 else ''

        if password:
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cur.execute("UPDATE users SET first_name=%s, last_name=%s, email=%s, password=%s, role=%s, assigned_location=%s WHERE id=%s", (_admin_first, _admin_last, email, hashed_pw, role, assigned_location, user_id))

        else:

            cur.execute("UPDATE users SET first_name=%s, last_name=%s, email=%s, role=%s, assigned_location=%s WHERE id=%s", (_admin_first, _admin_last, email, role, assigned_location, user_id))

        

        commit_db()



        # Log activity

        log_activity(

            admin_id=requester_id,

            admin_name=requester['full_name'] if 'full_name' in requester else 'Super Admin',

            action='UPDATE_STAFF',

            target_type='STAFF',

            target_id=str(user_id),

            details=f"Updated staff account: {name}"

        )



        return jsonify({"message": "Admin updated"}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 400

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/admin/delete/<int:user_id>', methods=['DELETE'])

def delete_admin(user_id):

    requester_id = request.args.get('requester_id')

    try:

        cur = get_cursor()

        cur.execute("SELECT full_name, role FROM users WHERE id=%s", (requester_id,))

        requester = cur.fetchone()

        if not requester or requester['role'] != 'super_admin':

            return jsonify({"error": "Unauthorized"}), 403



        # Prevent deleting super_admin accounts
        cur.execute("SELECT role FROM users WHERE id=%s", (user_id,))
        target = cur.fetchone()
        if target and target['role'] == 'super_admin':
            return jsonify({"error": "Super Admin accounts cannot be deleted."}), 403


        cur.execute("DELETE FROM users WHERE id=%s AND id != %s", (user_id, requester_id))

        commit_db()



        # Log activity

        log_activity(

            admin_id=requester_id,

            admin_name=requester['full_name'] if 'full_name' in requester else 'Super Admin',

            action='DELETE_STAFF',

            target_type='STAFF',

            target_id=str(user_id),

            details=f"Deleted staff account ID: {user_id}"

        )



        return jsonify({"message": "Admin deleted"}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 400

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/admin/status/<int:user_id>', methods=['PUT'])

def toggle_admin_status(user_id):

    data = request.json

    requester_id = data.get('requester_id')

    new_status = data.get('status')

    try:

        cur = get_cursor()

        cur.execute("SELECT full_name, role FROM users WHERE id=%s", (requester_id,))

        requester = cur.fetchone()

        if not requester or requester['role'] != 'super_admin':

            return jsonify({"error": "Unauthorized"}), 403



        # Prevent toggling super_admin status
        cur.execute("SELECT role FROM users WHERE id=%s", (user_id,))
        target = cur.fetchone()
        if target and target['role'] == 'super_admin':
            return jsonify({"error": "Super Admin status cannot be changed."}), 403


        cur.execute("UPDATE users SET is_verified=%s WHERE id=%s AND id != %s", (new_status, user_id, requester_id))

        commit_db()



        # Log activity

        log_activity(

            admin_id=requester_id,

            admin_name=requester['full_name'] if 'full_name' in requester else 'Super Admin',

            action='TOGGLE_STAFF_STATUS',

            target_type='STAFF',

            target_id=str(user_id),

            details=f"Set staff ID {user_id} status to {'Active' if new_status == 1 else 'Disabled'}"

        )



        return jsonify({"message": "Status updated"}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 400

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/admin/create', methods=['POST'])

def create_admin():

    data = request.json

    requester_id = data.get('requester_id') # Matches frontend

    name = data.get('name')

    email = data.get('email')

    password = data.get('password')

    role = data.get('role', 'admin')

    assigned_location = data.get('assigned_location')



    try:

        cur = get_cursor()

        # Verify requester is Super Admin

        cur.execute("SELECT full_name, role FROM users WHERE id=%s", (requester_id,))

        requester = cur.fetchone()

        if not requester or requester['role'] != 'super_admin':

            return jsonify({"error": "Unauthorized. Only Super Admin can create admin accounts."}), 403



        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        # Split name into first/last for generated full_name column
        _admin_name_parts = (name or '').strip().split(' ', 1)
        _admin_first = _admin_name_parts[0] if _admin_name_parts else name
        _admin_last = _admin_name_parts[1] if len(_admin_name_parts) > 1 else ''
        cur.execute("""
            INSERT INTO users (first_name, last_name, email, password, role, assigned_location, is_email_verified, is_verified)
            VALUES (%s, %s, %s, %s, %s, %s, True, 1)
            RETURNING id
        """, (_admin_first, _admin_last, email, hashed_pw, role, assigned_location))

        new_id = cur.fetchone()['id']

        commit_db()



        # Log activity

        log_activity(

            admin_id=requester_id,

            admin_name=requester['full_name'] if requester and 'full_name' in requester else 'Super Admin',

            action='CREATE_STAFF',

            target_type='STAFF',

            target_id=str(new_id),

            details=f"Created {role} account: {name} ({email})"

        )



        return jsonify({"message": f"Admin account created for {name}"}), 201

    except Exception as e:

        error_msg = str(e)

        if "unique constraint" in error_msg.lower() and "email" in error_msg.lower():

            return jsonify({"error": "This email is already in use. Please use a different one."}), 400

        return jsonify({"error": error_msg}), 400

    finally:

        if 'cur' in locals(): cur.close()





@app.route('/vehicles', methods=['GET'], strict_slashes=False)

def get_vehicles():

    try:

        cur = get_cursor()

        cur.execute("SELECT * FROM vehicles ORDER BY id DESC")

        data = cur.fetchall()

        vehicles = []

        for v in data:

            v_dict = {k: (float(val) if hasattr(val, '__float__') and not isinstance(val, (int, bool, float)) else (str(val) if hasattr(val, 'isoformat') else val)) for k, val in dict(v).items()}

            try:

                cur.execute("SELECT id, image_path FROM vehicle_images WHERE vehicle_id = %s ORDER BY order_index ASC, id ASC", (v['id'],))

            except Exception:

                cur.execute("SELECT id, image_path FROM vehicle_images WHERE vehicle_id = %s ORDER BY id ASC", (v['id'],))

            v_dict['gallery_details'] = [dict(r) for r in cur.fetchall()]

            vehicles.append(v_dict)

        return jsonify(vehicles), 200

    except Exception as e:

        import traceback

        print(f"ERROR in get_vehicles: {traceback.format_exc()}")

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/vehicles', methods=['POST'])
def add_vehicle():
    # Support both JSON and FormData
    if request.is_json:
        data = request.json
    else:
        data = request.form
    try:
        cur = get_cursor()
        # Ensure vehicle monitoring columns exist
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS color VARCHAR(50) DEFAULT NULL")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS mileage_type VARCHAR(20) DEFAULT 'limited'")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS mileage_km_per_day INT DEFAULT 250")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS year_model INT DEFAULT NULL")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS odometer INT DEFAULT 0")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS fuel_level VARCHAR(20) DEFAULT 'Full Tank'")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS next_service_schedule DATE DEFAULT NULL")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS lto_expiry_date DATE DEFAULT NULL")
        
        color = data.get('color') or None
        mileage_type = data.get('mileage_type') or 'limited'
        mileage_km_per_day = data.get('mileage_km_per_day') or 250
        year_model = data.get('year_model') or None
        odometer = data.get('odometer') or 0
        fuel_level = data.get('fuel_level') or 'Full Tank'
        next_service_schedule = data.get('next_service_schedule') or None
        lto_expiry_date = data.get('lto_expiry_date') or None

        # Handle image upload if file provided
        vehicle_image = data.get('vehicle_image', '')
        if 'gallery' in request.files:
            files = request.files.getlist('gallery')
            if files and files[0].filename:
                file = files[0]
                filename = 'vehicle_' + str(__import__('time').time()) + '_' + file.filename
                file_data = file.read()
                try:
                    supabase.storage.from_('uploads').upload(path=filename, file=file_data, file_options={"content-type": file.content_type})
                    vehicle_image = supabase.storage.from_('uploads').get_public_url(filename)
                except Exception:
                    pass
        cur.execute(
            "INSERT INTO vehicles (brand, model, plate_number, vehicle_type, transmission, fuel_type, seats, location, status, daily_rate, vehicle_image, color, mileage_type, mileage_km_per_day, year_model, odometer, fuel_level, next_service_schedule, lto_expiry_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (data.get('brand'), data.get('model'), data.get('plate_number'), data.get('vehicle_type'),
             data.get('transmission'), data.get('fuel_type'), data.get('seats'), data.get('location'),
             data.get('status', 'Available'), data.get('daily_rate'), vehicle_image, color, mileage_type, mileage_km_per_day, year_model,
             odometer, fuel_level, next_service_schedule, lto_expiry_date)
        )
        new_id = cur.fetchone()['id']
        # Handle additional gallery files
        if 'gallery' in request.files:
            files = request.files.getlist('gallery')
            for i, f in enumerate(files):
                if f.filename:
                    fname = 'gallery_' + str(new_id) + '_' + str(i) + '_' + f.filename
                    fdata = f.read()
                    try:
                        supabase.storage.from_('uploads').upload(path=fname, file=fdata, file_options={"content-type": f.content_type})
                        img_url = supabase.storage.from_('uploads').get_public_url(fname)
                        cur.execute("INSERT INTO vehicle_images (vehicle_id, image_path, order_index) VALUES (%s, %s, %s)", (new_id, img_url, i))
                    except Exception:
                        pass
        commit_db()
        return jsonify({"message": "Vehicle added", "id": new_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/vehicles/<int:vehicle_id>', methods=['PUT'])
def update_vehicle(vehicle_id):
    # Support both JSON and FormData
    if request.is_json:
        data = request.json
    else:
        data = request.form
    try:
        cur = get_cursor()
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS color VARCHAR(50) DEFAULT NULL")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS mileage_type VARCHAR(20) DEFAULT 'limited'")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS mileage_km_per_day INT DEFAULT 250")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS year_model INT DEFAULT NULL")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS odometer INT DEFAULT 0")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS fuel_level VARCHAR(20) DEFAULT 'Full Tank'")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS next_service_schedule DATE DEFAULT NULL")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS lto_expiry_date DATE DEFAULT NULL")
        
        color = data.get('color') or None
        mileage_type = data.get('mileage_type') or 'limited'
        mileage_km_per_day = data.get('mileage_km_per_day') or 250
        year_model = data.get('year_model') or None
        odometer = data.get('odometer') or 0
        fuel_level = data.get('fuel_level') or 'Full Tank'
        next_service_schedule = data.get('next_service_schedule') or None
        lto_expiry_date = data.get('lto_expiry_date') or None

        # Fetch existing vehicle_image from DB so it's preserved if no new photo is uploaded
        cur.execute("SELECT vehicle_image FROM vehicles WHERE id = %s", (vehicle_id,))
        existing = cur.fetchone()
        vehicle_image = existing['vehicle_image'] if existing else ''
        # Override with form-provided value if explicitly set (non-empty)
        form_image = data.get('vehicle_image', '')
        if form_image:
            vehicle_image = form_image
        if 'gallery' in request.files:
            files = request.files.getlist('gallery')
            for i, f in enumerate(files):
                if f.filename:
                    filename = 'vehicle_' + str(vehicle_id) + '_' + str(__import__('time').time()) + '_' + str(i) + '_' + f.filename
                    file_data = f.read()
                    try:
                        supabase.storage.from_('uploads').upload(path=filename, file=file_data, file_options={"content-type": f.content_type})
                        img_url = supabase.storage.from_('uploads').get_public_url(filename)
                        cur.execute("INSERT INTO vehicle_images (vehicle_id, image_path, order_index) VALUES (%s, %s, %s)", (vehicle_id, img_url, i))
                        if i == 0:
                            vehicle_image = img_url  # Update main image to first new photo
                    except Exception:
                        pass
        cur.execute(
            "UPDATE vehicles SET brand=%s, model=%s, plate_number=%s, vehicle_type=%s, transmission=%s, fuel_type=%s, seats=%s, location=%s, status=%s, daily_rate=%s, vehicle_image=%s, color=%s, mileage_type=%s, mileage_km_per_day=%s, year_model=%s, odometer=%s, fuel_level=%s, next_service_schedule=%s, lto_expiry_date=%s WHERE id=%s",
            (data.get('brand'), data.get('model'), data.get('plate_number'), data.get('vehicle_type'),
             data.get('transmission'), data.get('fuel_type'), data.get('seats'), data.get('location'),
             data.get('status'), data.get('daily_rate'), vehicle_image, color, mileage_type, mileage_km_per_day, year_model,
             odometer, fuel_level, next_service_schedule, lto_expiry_date, vehicle_id)
        )
        commit_db()
        return jsonify({"message": "Vehicle updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/vehicles/<int:vehicle_id>/status', methods=['PATCH', 'PUT'])
def update_vehicle_status(vehicle_id):
    data = request.json or request.form
    new_status = data.get('status')
    if not new_status:
        return jsonify({"error": "Status is required"}), 400
    try:
        cur = get_cursor()
        cur.execute("UPDATE vehicles SET status = %s WHERE id = %s", (new_status, vehicle_id))
        commit_db()
        return jsonify({"message": "Status updated successfully", "status": new_status}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()



@app.route('/vehicles/<int:vehicle_id>', methods=['DELETE'])

def delete_vehicle(vehicle_id):

    # Require super_admin to delete vehicles
    admin_id = request.args.get('admin_id') or (request.get_json(silent=True) or {}).get('admin_id')

    try:

        cur = get_cursor()

        if admin_id:
            cur.execute("SELECT role FROM users WHERE id = %s", (admin_id,))
            requester = cur.fetchone()
            if not requester or requester['role'] != 'super_admin':
                return jsonify({'error': 'Unauthorized. Only Super Admin can delete vehicles.'}), 403

        cur.execute("DELETE FROM vehicle_images WHERE vehicle_id = %s", (vehicle_id,))

        cur.execute("DELETE FROM vehicles WHERE id = %s", (vehicle_id,))

        commit_db()

        return jsonify({"message": "Vehicle deleted"}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/vehicles/check-availability', methods=['POST'])
def check_vehicle_availability():
    """
    Check if a vehicle has any conflicting bookings for the requested dates.
    Returns:
      - available: True if no conflict
      - conflict: details of the conflicting booking (nearest one that overlaps)
      - next_available_from: the date after the conflicting booking ends
    """
    try:
        data = request.get_json() or {}
        vehicle_id = data.get('vehicle_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not vehicle_id or not start_date or not end_date:
            return jsonify({'error': 'vehicle_id, start_date, and end_date are required'}), 400

        cur = get_cursor()

        # Find any overlapping active bookings
        cur.execute("""
            SELECT id, start_date, end_date, status,
                   (end_date + INTERVAL '1 day')::date as next_available
            FROM bookings
            WHERE vehicle_id = %s
              AND status IN ('Pending', 'Confirmed', 'Approved', 'Picked Up', 'Ongoing')
              AND start_date <= %s
              AND end_date >= %s
            ORDER BY start_date ASC
            LIMIT 1
        """, (vehicle_id, end_date, start_date))

        conflict = cur.fetchone()

        if conflict:
            c = dict(conflict)
            return jsonify({
                'available': False,
                'conflict': {
                    'booking_id': c['id'],
                    'start_date': str(c['start_date']),
                    'end_date': str(c['end_date']),
                    'status': c['status']
                },
                'next_available_from': str(c['next_available'])
            }), 200

        # Also check if the requested end_date is close to a future booking
        # so we can warn the user about extending limits
        cur.execute("""
            SELECT id, start_date, end_date, status
            FROM bookings
            WHERE vehicle_id = %s
              AND status IN ('Pending', 'Confirmed', 'Approved', 'Picked Up', 'Ongoing')
              AND start_date > %s
            ORDER BY start_date ASC
            LIMIT 1
        """, (vehicle_id, end_date))

        upcoming = cur.fetchone()
        upcoming_info = None
        if upcoming:
            u = dict(upcoming)
            upcoming_info = {
                'start_date': str(u['start_date']),
                'end_date': str(u['end_date']),
                'status': u['status']
            }

        return jsonify({
            'available': True,
            'next_booking': upcoming_info
        }), 200

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/vehicles/categories', methods=['GET'], strict_slashes=False)


def get_vehicle_categories():

    try:

        cur = get_cursor()

        cur.execute("""

            SELECT 

                MIN(id) as id,

                brand,

                model,

                -- Use image from first AVAILABLE unit (not in permanent out-of-service states)
                -- Falls back to any unit image if none are available
                COALESCE(
                    MIN(CASE WHEN status NOT IN ('Maintenance','Repair','Service','Sold') THEN vehicle_image END),
                    MIN(vehicle_image)
                ) as vehicle_image,

                MIN(daily_rate) as daily_rate,

                MIN(vehicle_type) as vehicle_type,

                MIN(seats) as seats,

                MIN(fuel_type) as fuel_type,

                MIN(transmission) as transmission,

                MIN(location) as location,

                COUNT(*) as total_units,

                -- Count units that are operationally available (not permanently out of service).
                -- 'Rented' is intentionally included because a car booked for June 25-26 is
                -- still bookable for other dates — overlap is enforced at booking time, not here.
                SUM(CASE WHEN status NOT IN ('Maintenance','Repair','Service','Sold') THEN 1 ELSE 0 END) as available_units

            FROM vehicles

            WHERE status != 'Sold'

            GROUP BY brand, model

            ORDER BY brand, model

        """)

        categories = cur.fetchall()

        result = []

        for c in categories:

            d = dict(c)

            # Convert Decimal to float for JSON serialization

            if d.get('daily_rate'):

                d['daily_rate'] = float(d['daily_rate'])

            d['available_units'] = int(d.get('available_units') or 0)

            d['total_units'] = int(d.get('total_units') or 0)

            result.append(d)

        return jsonify(result), 200

    except Exception as e:

        import traceback

        print(f"ERROR in get_vehicle_categories: {traceback.format_exc()}")

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/vehicles/<int:vehicle_id>', methods=['GET'])

def get_vehicle_details_v2(vehicle_id):

    user_id = request.args.get('user_id')

    try:

        cur = get_cursor()

        cur.execute("SELECT * FROM vehicles WHERE id = %s", (vehicle_id,))

        vehicle = cur.fetchone()

        if not vehicle:

            return jsonify({"error": "Vehicle not found"}), 404

        v_dict = dict(vehicle)



        # Reviews

        cur.execute("""

            SELECT r.*, u.full_name, u.profile_picture 

            FROM reviews r

            JOIN users u ON r.user_id = u.id

            WHERE r.vehicle_id = %s

            ORDER BY r.created_at DESC

        """, (vehicle_id,))

        v_dict['reviews'] = [dict(r) for r in cur.fetchall()]



        # Avg Rating

        cur.execute("SELECT AVG(rating) as avg_rating FROM reviews WHERE vehicle_id = %s", (vehicle_id,))

        avg_row = cur.fetchone()

        avg = avg_row['avg_rating'] if avg_row else None

        v_dict['avg_rating'] = float(avg) if avg else 0



        # Favorite status

        v_dict['is_favorite'] = False

        if user_id and user_id != 'null':

            cur.execute("SELECT 1 FROM favorites WHERE user_id = %s AND vehicle_id = %s", (user_id, vehicle_id))

            if cur.fetchone():

                v_dict['is_favorite'] = True



        # Gallery Images

        try:

            cur.execute("SELECT id, image_path, is_primary, order_index FROM vehicle_images WHERE vehicle_id = %s ORDER BY order_index ASC, id ASC", (vehicle_id,))

            gallery_images = cur.fetchall()

        except Exception:

            cur.execute("SELECT id, image_path, is_primary, id as order_index FROM vehicle_images WHERE vehicle_id = %s ORDER BY id ASC", (vehicle_id,))

            gallery_images = cur.fetchall()



        v_dict['gallery'] = [row['image_path'] for row in gallery_images]

        v_dict['gallery_details'] = [dict(row) for row in gallery_images]



        # Pickup Instructions

        try:

            cur.execute("SELECT description FROM pickup_instructions")

            instructions = cur.fetchall()

            v_dict['pickup_instructions'] = [row['description'] for row in instructions]

        except Exception:

            v_dict['pickup_instructions'] = []



        return jsonify(v_dict), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/admin/stats', methods=['GET'], strict_slashes=False)

def get_admin_stats_v2():

    admin_id = request.args.get('admin_id')

    try:

        cur = get_cursor()

        cur.execute("SELECT role, assigned_location FROM users WHERE id=%s", (admin_id,))

        adm = cur.fetchone()

        location_filter = adm['assigned_location'] if adm and adm['role'] == 'admin' else None

        

        stats = {"total_revenue": 0, "total_bookings": 0, "active_vehicles": 0}

        rev_q = "SELECT SUM(total_price) as rev FROM bookings WHERE payment_status = 'Paid'"

        book_q = "SELECT COUNT(*) as count FROM bookings"

        v_q = "SELECT COUNT(*) as count FROM vehicles WHERE status = 'Available'"

        

        if location_filter:

            cur.execute(rev_q + " AND pickup_location = %s", (location_filter,))

            stats['total_revenue'] = float(cur.fetchone()['rev'] or 0)

            cur.execute(book_q + " AND pickup_location = %s", (location_filter,))

            stats['total_bookings'] = int(cur.fetchone()['count'] or 0)

            cur.execute(v_q + " AND location = %s", (location_filter,))

            stats['active_vehicles'] = int(cur.fetchone()['count'] or 0)

        else:

            cur.execute(rev_q); stats['total_revenue'] = float(cur.fetchone()['rev'] or 0)

            cur.execute(book_q); stats['total_bookings'] = int(cur.fetchone()['count'] or 0)

            cur.execute(v_q); stats['active_vehicles'] = int(cur.fetchone()['count'] or 0)



        # Revenue trend

        cur.execute("SELECT DATE(start_date) as day, SUM(total_price) as amount FROM bookings WHERE payment_status = 'Paid' GROUP BY day ORDER BY day DESC LIMIT 7")

        trend = [{"day": str(t['day']), "amount": float(t['amount'] or 0)} for t in cur.fetchall()]

            

        # Fleet distribution

        cur.execute("SELECT status, COUNT(*) as count FROM vehicles GROUP BY status")

        fleet = [{"status": f['status'], "count": int(f['count'])} for f in cur.fetchall()]



        # Booking status breakdown

        cur.execute("SELECT status, COUNT(*) as count FROM bookings GROUP BY status")

        booking_breakdown = {r['status'].lower(): int(r['count']) for r in cur.fetchall()}



        # User verification stats (Currently unused in dashboard frontend)
        user_stats = {
            "email": {"verified": 0, "unverified": 0},
            "license": {"approved": 0, "pending": 0, "rejected": 0}
        }



        # Top grossing vehicles

        try:
            cur.execute("""
                SELECT v.brand, v.model, v.plate_number,
                       COUNT(b.id) as booking_count,
                       COALESCE(SUM(b.total_price), 0) as revenue
                FROM vehicles v
                LEFT JOIN bookings b ON b.vehicle_id = v.id AND b.payment_status = 'Paid'
                GROUP BY v.id, v.brand, v.model, v.plate_number
                ORDER BY revenue DESC
                LIMIT 5
            """)
            top_vehicles = [{"brand": r.get('brand'), "model": r.get('model'), "plate_number": r.get('plate_number'), "booking_count": int(r.get('booking_count') or 0), "revenue": float(r.get('revenue') or 0)} for r in cur.fetchall()]
        except Exception as e:
            print("ERROR in topVehicles query:", e)
            top_vehicles = []


        

        return jsonify({

            "summary": stats, 

            "total_revenue": stats['total_revenue'], 

            "total_bookings": stats['total_bookings'],

            "revenueTrend": trend, 

            "fleetDistribution": fleet,

            "bookingsByStatus": booking_breakdown,

            "userStats": user_stats,

            "topVehicles": top_vehicles

        }), 200

    except Exception as e: 

        print(f"ERROR in get_admin_stats: {e}")

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/admin/dashboard-stats', methods=['GET'])

def get_admin_detailed_stats():

    admin_id = request.args.get('admin_id')

    try:

        cur = get_cursor()

        cur.execute("SELECT role, assigned_location FROM users WHERE id=%s", (admin_id,))

        admin = cur.fetchone()

        

        if not admin or admin['role'] not in ['admin', 'super_admin']:

            return jsonify({"error": "Forbidden"}), 403



        location_filter = admin['assigned_location'] if admin['role'] == 'admin' else None



        bk_query = "SELECT COUNT(*) as count FROM bookings b"

        vh_query = "SELECT COUNT(*) as count FROM vehicles v"

        params = []



        if location_filter:

            bk_query += " WHERE b.pickup_location = %s"

            vh_query += " WHERE v.location = %s"

            params.append(location_filter)



        cur.execute(bk_query, tuple(params))

        total_bookings = cur.fetchone()['count']

        

        cur.execute(vh_query, tuple(params))

        total_vehicles = cur.fetchone()['count']



        stats = {

            "total_bookings": total_bookings,

            "total_vehicles": total_vehicles,

            "role": admin['role']

        }



        rev_query = "SELECT SUM(total_price) as revenue FROM bookings b"

        if location_filter:

            rev_query += " WHERE b.pickup_location = %s AND b.status = 'Confirmed'"

        else:

            rev_query += " WHERE b.status = 'Confirmed'"

            

        cur.execute(rev_query, tuple(params))

        revenue = cur.fetchone()['revenue'] or 0

        stats["total_revenue"] = float(revenue)



        return jsonify(stats), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 400

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/admin/change-password', methods=['POST'])

def change_admin_password():

    data = request.json

    user_id = data.get('user_id')

    new_password = data.get('new_password')



    if not user_id or not new_password:

        return jsonify({"error": "Missing user_id or password"}), 400



    try:

        cur = get_cursor()

        cur.execute("SELECT id, role FROM users WHERE id=%s", (user_id,))

        user = cur.fetchone()

        if not user or user['role'] not in ['admin', 'super_admin']:

            return jsonify({"error": "Unauthorized"}), 403



        hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute("UPDATE users SET password=%s WHERE id=%s", (hashed_pw, user_id))
        commit_db()
        return jsonify({"message": "Password updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if 'cur' in locals(): cur.close()

        

@app.route('/admin/settings', methods=['GET', 'POST'])

def handle_admin_settings():

    """Unified endpoint for viewing and updating system settings."""

    if request.method == 'GET':

        try:

            cur = get_cursor()

            cur.execute("SELECT key, value, description FROM settings ORDER BY key ASC")

            settings = cur.fetchall()

            return jsonify([dict(s) for s in settings]), 200

        except Exception as e:

            return jsonify({"error": str(e)}), 400

        finally:

            if 'cur' in locals(): cur.close()

    

    elif request.method == 'POST':

        data = request.json

        requester_id = data.get('requester_id')

        updates = data.get('settings', [])



        if not requester_id or not updates:

            return jsonify({"error": "Missing requester_id or settings"}), 400



        try:

            cur = get_cursor()

            cur.execute("SELECT full_name, role FROM users WHERE id=%s", (requester_id,))

            user = cur.fetchone()

            if not user or user['role'] != 'super_admin':

                return jsonify({"error": "Unauthorized. Super Admin only."}), 403



            for item in updates:

                cur.execute("UPDATE settings SET value=%s, updated_at=CURRENT_TIMESTAMP WHERE key=%s", (str(item['value']), item['key']))

            

            commit_db()



            log_activity(

                admin_id=requester_id,

                admin_name=user['full_name'],

                action='UPDATE_SYSTEM_SETTINGS',

                target_type='SYSTEM',

                details=f"Updated {len(updates)} system settings."

            )



            return jsonify({"message": "Settings updated successfully"}), 200

        except Exception as e:

            return jsonify({"error": str(e)}), 400

        finally:

            if 'cur' in locals(): cur.close()



@app.route('/locations', methods=['GET'])
def get_locations():
    try:
        cur = get_cursor()
        cur.execute("SELECT id, name, province, municipality, barangay, delivery_fee FROM locations ORDER BY name ASC")
        rows = cur.fetchall()
        return jsonify([dict(r) for r in rows]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/admin/locations', methods=['POST'])
def add_location():
    try:
        data = request.json or {}
        requester_id = data.get('requester_id')
        name = data.get('name')
        province = data.get('province', '')
        municipality = data.get('municipality', '')
        barangay = data.get('barangay', '')
        delivery_fee = float(data.get('delivery_fee', 0.00))

        if not requester_id or not name:
            return jsonify({"error": "Missing requester_id or name"}), 400

        cur = get_cursor()
        cur.execute("SELECT full_name, role FROM users WHERE id=%s", (requester_id,))
        user = cur.fetchone()
        if not user or user['role'] != 'super_admin':
            return jsonify({"error": "Unauthorized. Super Admin only."}), 403

        cur.execute("""
            INSERT INTO locations (name, province, municipality, barangay, delivery_fee)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (name, province, municipality, barangay, delivery_fee))
        new_id = cur.fetchone()['id']
        commit_db()

        log_activity(
            admin_id=requester_id,
            admin_name=user['full_name'],
            action='ADD_LOCATION',
            target_type='LOCATION',
            target_id=str(new_id),
            details=f"Added location: {name} with fee ₱{delivery_fee}"
        )
        return jsonify({"message": "Location added successfully", "id": new_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/admin/locations/<int:loc_id>', methods=['PUT', 'DELETE'])
def handle_location_detail(loc_id):
    try:
        data = request.json or {}
        requester_id = data.get('requester_id') or request.args.get('requester_id')

        if not requester_id:
            return jsonify({"error": "Missing requester_id"}), 400

        cur = get_cursor()
        cur.execute("SELECT full_name, role FROM users WHERE id=%s", (requester_id,))
        user = cur.fetchone()
        if not user or user['role'] != 'super_admin':
            return jsonify({"error": "Unauthorized. Super Admin only."}), 403

        if request.method == 'PUT':
            name = data.get('name')
            province = data.get('province', '')
            municipality = data.get('municipality', '')
            barangay = data.get('barangay', '')
            delivery_fee = float(data.get('delivery_fee', 0.00))

            if not name:
                return jsonify({"error": "Missing location name"}), 400

            cur.execute("""
                UPDATE locations
                SET name=%s, province=%s, municipality=%s, barangay=%s, delivery_fee=%s
                WHERE id=%s
            """, (name, province, municipality, barangay, delivery_fee, loc_id))
            commit_db()

            log_activity(
                admin_id=requester_id,
                admin_name=user['full_name'],
                action='UPDATE_LOCATION',
                target_type='LOCATION',
                target_id=str(loc_id),
                details=f"Updated location: {name} (Fee: ₱{delivery_fee})"
            )
            return jsonify({"message": "Location updated successfully"}), 200

        elif request.method == 'DELETE':
            cur.execute("SELECT name FROM locations WHERE id=%s", (loc_id,))
            loc_row = cur.fetchone()
            if not loc_row:
                return jsonify({"error": "Location not found"}), 404

            cur.execute("DELETE FROM locations WHERE id=%s", (loc_id,))
            commit_db()

            log_activity(
                admin_id=requester_id,
                admin_name=user['full_name'],
                action='DELETE_LOCATION',
                target_type='LOCATION',
                target_id=str(loc_id),
                details=f"Deleted location: {loc_row['name']}"
            )
            return jsonify({"message": "Location deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/admin/activity-logs', methods=['GET'])
def get_activity_logs():
    try:
        cur = get_cursor()
        page = request.args.get('page')
        limit = request.args.get('limit')

        if page:
            page = int(page)
            limit = int(limit) if limit else 50
            offset = (page - 1) * limit

            # Get total count
            cur.execute("SELECT COUNT(*) as total FROM activity_logs")
            total = cur.fetchone()['total']

            # Get paginated logs
            cur.execute("SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT %s OFFSET %s", (limit, offset))
            logs = cur.fetchall()

            return jsonify({
                "logs": logs,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }), 200
        else:
            cur.execute("SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT 100")
            logs = cur.fetchall()
            return jsonify(logs), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if 'cur' in locals(): cur.close()



@app.route('/public/settings', methods=['GET'])

def get_public_settings():

    """Returns non-sensitive system settings for the customer app."""

    try:

        cur = get_cursor()

        public_keys = [
            'mileage_limit', 
            'long_term_discount_days', 
            'long_term_discount_percent',
            'currency',
            'rental_terms',
            'loyalty_points_spend_ratio',
            'loyalty_points_value',
            'loyalty_max_discount_percent'
        ]

        cur.execute("SELECT key, value FROM settings WHERE key = ANY(%s)", (public_keys,))

        settings = cur.fetchall()

        return jsonify({s['key']: s['value'] for s in settings}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 400

    finally:

        if 'cur' in locals(): cur.close()





# ==================== CUSTOMER GPS ENDPOINT ====================



@app.route('/vehicles/<int:vehicle_id>/location', methods=['GET'])

def get_vehicle_location_for_customer(vehicle_id):

    """

    Customer-facing GPS endpoint.

    Returns latitude, longitude, and last_gps_update for a specific vehicle.

    Only accessible if the requesting user has an active booking for this vehicle.

    """

    user_id = request.args.get('user_id')

    if not user_id:

        return jsonify({"error": "user_id is required"}), 400



    try:

        cur = get_cursor()



        # Security: verify the user has an active booking for this vehicle

        cur.execute("""

            SELECT id FROM bookings

            WHERE vehicle_id = %s

              AND user_id = %s

              AND status IN ('Confirmed', 'Approved', 'Picked Up')

            LIMIT 1

        """, (vehicle_id, user_id))

        booking = cur.fetchone()



        if not booking:

            return jsonify({

                "error": "Access denied. No active booking found for this vehicle."

            }), 403



        # Fetch GPS data

        cur.execute(

            "SELECT latitude, longitude, last_gps_update FROM vehicles WHERE id = %s",

            (vehicle_id,)

        )

        vehicle = cur.fetchone()



        if not vehicle:

            return jsonify({"error": "Vehicle not found"}), 404



        return jsonify({

            "vehicle_id": vehicle_id,

            "latitude": vehicle['latitude'],

            "longitude": vehicle['longitude'],

            "last_gps_update": str(vehicle['last_gps_update']) if vehicle['last_gps_update'] else None

        }), 200



    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=True)

    app.run(host='0.0.0.0', port=9999, debug=True)



# ==================== COLOR SELECTION AND VEHICLE UNITS ====================

@app.route('/vehicles/colors', methods=['GET'])
def get_vehicle_colors():
    """Get available colors for a brand+model."""
    brand = request.args.get('brand', '')
    model = request.args.get('model', '')
    if not brand or not model:
        return jsonify({'error': 'brand and model are required'}), 400
    try:
        cur = get_cursor()
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS color VARCHAR(50) DEFAULT NULL")
        commit_db()
        cur.execute(
            "SELECT DISTINCT COALESCE(color, 'Not Specified') as color, COUNT(*) as total, "
            "SUM(CASE WHEN status NOT IN ('Maintenance','Repair','Service','Sold') THEN 1 ELSE 0 END) as available "
            "FROM vehicles WHERE brand = %s AND model = %s GROUP BY color ORDER BY color",
            (brand, model)
        )
        colors = cur.fetchall()
        return jsonify([dict(c) for c in colors]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/vehicles/units', methods=['GET'])
def get_vehicle_units():
    """Get all individual units for a brand+model, optionally filtered by color. Only shows available units."""
    brand = request.args.get('brand', '')
    model = request.args.get('model', '')
    color = request.args.get('color', '')
    user_id = request.args.get('user_id', '')
    if not brand or not model:
        return jsonify({'error': 'brand and model are required'}), 400

    try:
        cur = get_cursor()
        # Exclude permanently unavailable statuses only.
        # 'Rented' and 'Booked' are intentionally NOT excluded here — a vehicle rented for
        # June 25-26 is still bookable for other dates; overlap is enforced at submit time.
        unavailable = ['Maintenance', 'Repair', 'Service', 'Sold']
        placeholders = ','.join(['%s'] * len(unavailable))

        if color and color != 'all' and color != 'Not Specified':
            cur.execute(
                f"SELECT * FROM vehicles WHERE brand = %s AND model = %s AND COALESCE(color, 'Not Specified') = %s AND status NOT IN ({placeholders}) ORDER BY id ASC",
                [brand, model, color] + unavailable
            )
        else:
            cur.execute(
                f"SELECT * FROM vehicles WHERE brand = %s AND model = %s AND status NOT IN ({placeholders}) ORDER BY id ASC",
                [brand, model] + unavailable
            )
        units = cur.fetchall()
        result = []
        for u in units:
            d = dict(u)
            if d.get('daily_rate'):
                d['daily_rate'] = float(d['daily_rate'])
            d['color_display'] = d.get('color') or 'Not Specified'
            d['is_favorite'] = False
            if user_id:
                cur.execute("SELECT 1 FROM favorites WHERE user_id = %s AND vehicle_id = %s", (user_id, d['id']))
                if cur.fetchone():
                    d['is_favorite'] = True
            try:
                cur.execute("SELECT image_path FROM vehicle_images WHERE vehicle_id = %s ORDER BY order_index ASC, id ASC", (d['id'],))
                d['gallery'] = [g['image_path'] for g in cur.fetchall()]
            except Exception:
                d['gallery'] = []
            result.append(d)
        return jsonify(result), 200
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/user/profile-full', methods=['GET'])
def get_full_profile():
    """Get complete user profile including phone, email, license image and license details."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        cur = get_cursor()
        cur.execute(
            """SELECT id, full_name, email, phone, profile_picture, license_image_url,
                      is_verified, loyalty_points, password,
                      license_number, license_expiry, license_type
               FROM users WHERE id = %s""",
            (user_id,)
        )
        user = cur.fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        d = dict(user)
        d['has_password'] = bool(d.get('password'))
        d.pop('password', None)
        d['loyalty_points'] = int(d.get('loyalty_points') or 0)
        d['is_verified'] = int(d.get('is_verified') or 0)
        if d.get('license_expiry'):
            d['license_expiry'] = str(d['license_expiry'])
        return jsonify(d), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """Get user profile by ID for admin customer profile preview."""
    try:
        cur = get_cursor()
        cur.execute(
            """SELECT id, full_name, email, phone, profile_picture, license_image_url,
                      is_verified, loyalty_points,
                      license_number, license_expiry, license_type
               FROM users WHERE id = %s""",
            (user_id,)
        )
        user = cur.fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        d = dict(user)
        d['loyalty_points'] = int(d.get('loyalty_points') or 0)
        d['is_verified'] = int(d.get('is_verified') or 0)
        # Add profile_picture_url alias for consistency
        d['profile_picture_url'] = d.get('profile_picture')
        # Add name alias for consistency
        d['name'] = d.get('full_name')
        if d.get('license_expiry'):
            d['license_expiry'] = str(d['license_expiry'])
        return jsonify(d), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/user/update-license-info', methods=['POST'])
def update_license_info():
    """Update license details (number, expiry, type) and optionally upload a new license image."""
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        cur = get_cursor()
        license_number = request.form.get('license_number', '').strip() or None
        license_expiry  = request.form.get('license_expiry', '').strip() or None
        license_type    = request.form.get('license_type', '').strip() or None

        license_url = None
        if 'license' in request.files:
            file = request.files['license']
            if file.filename:
                filename = f"license_{user_id}_{int(datetime.now().timestamp())}.jpg"
                file_data = file.read()
                try:
                    supabase.storage.from_('uploads').upload(path=filename, file=file_data,
                        file_options={"content-type": "image/jpeg", "upsert": "true"})
                except Exception:
                    supabase.storage.from_('uploads').update(path=filename, file=file_data,
                        file_options={"content-type": "image/jpeg"})
                license_url = supabase.storage.from_('uploads').get_public_url(filename)

        if license_url:
            cur.execute(
                """UPDATE users SET license_number=%s, license_expiry=%s, license_type=%s,
                          license_image_url=%s, is_verified=1 WHERE id=%s""",
                (license_number, license_expiry, license_type, license_url, user_id)
            )
        else:
            cur.execute(
                "UPDATE users SET license_number=%s, license_expiry=%s, license_type=%s WHERE id=%s",
                (license_number, license_expiry, license_type, user_id)
            )
        commit_db()
        return jsonify({'message': 'License info updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()



@app.route('/admin/bookings/<int:booking_id>/license-details', methods=['GET'])
def get_booking_license_details(booking_id):
    try:
        cur = get_cursor()
        cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))
        b = cur.fetchone()
        if not b:
            return jsonify({'error': 'Booking not found'}), 404
        user_id = b['user_id']

        # Try license_details table first
        cur.execute("SELECT * FROM license_details WHERE user_id = %s", (user_id,))
        details = cur.fetchone()

        if details:
            result = dict(details)
            if result.get('expiry_date') and hasattr(result['expiry_date'], 'strftime'):
                result['expiry_date'] = result['expiry_date'].strftime('%Y-%m-%d')
            if result.get('date_of_birth') and hasattr(result['date_of_birth'], 'strftime'):
                result['date_of_birth'] = result['date_of_birth'].strftime('%Y-%m-%d')
            # Ensure consistent key name for frontend
            result['emergency_contact_relation'] = result.get('emergency_contact_relationship', '-')
            return jsonify(result), 200

        # Fall back to users table
        cur.execute("""
            SELECT full_name, license_number, license_expiry AS expiry_date,
                   license_image_url AS license_front_url
            FROM users WHERE id = %s
        """, (user_id,))
        user = cur.fetchone()
        if user and (user.get('license_number') or user.get('license_front_url') or user.get('full_name')):
            result = dict(user)
            if result.get('expiry_date') and hasattr(result['expiry_date'], 'strftime'):
                result['expiry_date'] = result['expiry_date'].strftime('%Y-%m-%d')
            result['emergency_contact_relation'] = '-'
            result['emergency_contact_relationship'] = '-'
            result['license_back_url'] = None
            return jsonify(result), 200

        return jsonify({}), 200
    except Exception as e:
        print(f"Error fetching license details for booking {booking_id}:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/admin/bookings/<int:booking_id>/payment-proof', methods=['GET'])
def get_booking_payment_proof(booking_id):
    """Return all payment records (with proof images) for a booking."""
    try:
        cur = get_cursor()
        cur.execute("""
            SELECT id, amount, method, reference_number, payment_proof, status
            FROM payments
            WHERE booking_id = %s
        """, (booking_id,))
        rows = cur.fetchall()
        result = []
        for row in rows:
            entry = dict(row)
            proof = entry.get('payment_proof') or ''
            if proof and not proof.startswith('http'):
                proof = f"https://autoride-booking-system.vercel.app/api/uploads/{proof}"
            entry['payment_proof_url'] = proof
            result.append(entry)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/admin/users/<int:user_id>/license-details', methods=['GET'])
def get_user_license_details(user_id):
    try:
        cur = get_cursor()
        cur.execute("SELECT * FROM license_details WHERE user_id = %s", (user_id,))
        details = cur.fetchone()
        if not details:
            return jsonify({}), 200
        if details.get('expiry_date') and hasattr(details['expiry_date'], 'strftime'):
            details['expiry_date'] = details['expiry_date'].strftime('%Y-%m-%d')
        if details.get('date_of_birth') and hasattr(details['date_of_birth'], 'strftime'):
            details['date_of_birth'] = details['date_of_birth'].strftime('%Y-%m-%d')
        return jsonify(details), 200
    except Exception as e:
        print(f"Error fetching license details for user {user_id}:", e)
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/user/license-details-test', methods=['GET'])
def test_license_details():
    """Test endpoint to verify the deployment is working."""
    return jsonify({
        'status': 'ok',
        'message': 'License details endpoint is working',
        'timestamp': str(datetime.now()),
        'version': '2.0'
    }), 200

@app.route('/user/license-details', methods=['GET'])
def get_license_details():
    """Get the full driver's license details for a user."""
    try:
        user_id = request.args.get('user_id')
        
        # Enhanced debugging for parameter validation
        debug_info = {
            'received_user_id': user_id,
            'user_id_type': type(user_id).__name__,
            'user_id_length': len(user_id) if user_id else 0,
            'request_args': dict(request.args),
            'method': request.method
        }
        
        if not user_id or user_id.strip() == '':
            return jsonify({
                'error': 'user_id required or empty',
                'debug': debug_info
            }), 400
        
        # Validate user_id is numeric
        try:
            user_id_int = int(user_id.strip())
            if user_id_int <= 0:
                return jsonify({
                    'error': 'user_id must be a positive integer',
                    'debug': debug_info
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'error': 'user_id must be a valid number',
                'debug': debug_info
            }), 400
        
        # Ultra-safe approach: minimal response
        response_data = {
            'user_id': user_id_int,
            'status': 'checking',
            'table_exists': False,
            'has_data': False,
            'debug': debug_info
        }
        
        try:
            cur = get_cursor()
            
            # Check if table exists with minimal query
            cur.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'license_details' LIMIT 1")
            table_exists = cur.fetchone()
            response_data['table_exists'] = bool(table_exists)
            
            if not table_exists:
                # Create table immediately if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS license_details (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) UNIQUE,
                        full_name VARCHAR(100),
                        date_of_birth DATE,
                        license_number VARCHAR(50),
                        expiry_date DATE,
                        issuing_country_state VARCHAR(50),
                        license_class VARCHAR(20),
                        emergency_contact_name VARCHAR(100),
                        emergency_contact_phone VARCHAR(20),
                        emergency_contact_relationship VARCHAR(50),
                        license_front_url TEXT,
                        license_back_url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                commit_db()
                response_data['table_created'] = True
                response_data['table_exists'] = True
            
            # Simple check for data existence
            cur.execute("SELECT COUNT(*) as count FROM license_details WHERE user_id = %s LIMIT 1", (user_id_int,))
            count_result = cur.fetchone()
            has_data = count_result and count_result['count'] > 0
            response_data['has_data'] = has_data
            
            if has_data:
                # Get data with strict limits
                cur.execute("""
                    SELECT id, user_id, 
                           SUBSTRING(full_name, 1, 50) as full_name,
                           date_of_birth::text as date_of_birth, 
                           SUBSTRING(license_number, 1, 20) as license_number,
                           expiry_date::text as expiry_date,
                           SUBSTRING(issuing_country_state, 1, 30) as issuing_country_state,
                           SUBSTRING(license_class, 1, 10) as license_class,
                           SUBSTRING(emergency_contact_name, 1, 50) as emergency_contact_name,
                           SUBSTRING(emergency_contact_phone, 1, 15) as emergency_contact_phone,
                           SUBSTRING(emergency_contact_relationship, 1, 20) as emergency_contact_relationship,
                           license_front_url,
                           license_back_url,
                           created_at::text as created_at,
                           updated_at::text as updated_at
                    FROM license_details 
                    WHERE user_id = %s 
                    LIMIT 1
                """, (user_id_int,))
                
                row = cur.fetchone()
                if row:
                    data = dict(row)
                    # Ensure all values are safe and handle None dates
                    for key, value in data.items():
                        if key not in ('license_front_url', 'license_back_url', 'license_image_url') and isinstance(value, str) and len(value) > 100:
                            data[key] = value[:97] + "..."
                        elif value is None:
                            data[key] = None
                    
                    # Add fallback license_image_url from users table for admin mobile compatibility
                    try:
                        cur.execute("SELECT license_image_url FROM users WHERE id = %s", (user_id_int,))
                        user_row = cur.fetchone()
                        if user_row and user_row.get('license_image_url'):
                            data['license_image_url'] = user_row['license_image_url']
                            print(f"Added fallback license_image_url: {data['license_image_url']}")
                        else:
                            data['license_image_url'] = ""
                    except Exception as fallback_err:
                        print(f"Fallback license_image_url fetch error: {fallback_err}")
                        data['license_image_url'] = ""
                    
                    response_data['data'] = data
            
        except Exception as db_error:
            error_msg = str(db_error)[:100]  # Limit error message
            response_data['db_error'] = error_msg
            
        finally:
            if 'cur' in locals():
                cur.close()
        
        # Ensure response is never too large
        import json
        import datetime
        
        def safe_serialize(obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
        
        try:
            response_json = json.dumps(response_data, default=safe_serialize)
            if len(response_json) > 10000:  # 10KB limit
                return jsonify({
                    'error': 'Response too large',
                    'user_id': user_id,
                    'table_exists': response_data.get('table_exists', False)
                }), 413
        except Exception as json_err:
            return jsonify({
                'error': f'JSON serialization error: {str(json_err)[:100]}',
                'user_id': user_id
            }), 500
        
        return jsonify(response_data), 200
        
    except Exception as e:
        # Ultimate fallback - minimal response
        error_msg = str(e)[:50]  # Very short error
        return jsonify({
            'error': error_msg,
            'user_id': request.args.get('user_id', 'unknown'),
            'debug': {
                'received_args': dict(request.args),
                'method': request.method,
                'error_type': type(e).__name__
            }
        }), 500

@app.route('/user/license-details', methods=['POST'])
def save_license_details():
    """Save or update full driver's license details."""
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
        
    try:
        cur = get_cursor()
        
        # Ensure the license_details table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS license_details (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) UNIQUE,
                full_name VARCHAR(255),
                date_of_birth DATE,
                license_number VARCHAR(100),
                expiry_date DATE,
                issuing_country_state VARCHAR(100),
                license_class VARCHAR(50),
                emergency_contact_name VARCHAR(255),
                emergency_contact_phone VARCHAR(50),
                emergency_contact_relationship VARCHAR(100),
                license_front_url TEXT,
                license_back_url TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        commit_db()
        
        # Get form data with length limits
        full_name = (request.form.get('full_name', '') or '')[:255]
        date_of_birth = request.form.get('date_of_birth', '') or None
        license_number = (request.form.get('license_number', '') or '')[:100]
        expiry_date = request.form.get('expiry_date', '') or None
        issuing_country_state = (request.form.get('issuing_country_state', '') or '')[:100]
        license_class = (request.form.get('license_class', '') or '')[:50]
        emergency_contact_name = (request.form.get('emergency_contact_name', '') or '')[:255]
        emergency_contact_phone = (request.form.get('emergency_contact_phone', '') or '')[:50]
        emergency_contact_relationship = (request.form.get('emergency_contact_relationship', '') or '')[:100]
        
        # Convert empty date strings to valid dates or None
        if date_of_birth == '' or date_of_birth == 'null':
            date_of_birth = '1990-01-01'  # Default date if not provided
        if expiry_date == '' or expiry_date == 'null':
            expiry_date = '2030-12-31'  # Default expiry if not provided
        
        front_url = (request.form.get('license_front_url', '') or '')[:1000]  # Limit URL length
        back_url = (request.form.get('license_back_url', '') or '')[:1000]   # Limit URL length

        # Handle file uploads if present with size limits
        def upload_img(file_key, prefix):
            if file_key in request.files and request.files[file_key].filename:
                file = request.files[file_key]
                
                # Check file size (max 5MB)
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                
                if file_size > 5 * 1024 * 1024:  # 5MB limit
                    raise ValueError(f"File {file_key} is too large. Maximum size is 5MB.")
                
                filename = f"{prefix}_{user_id}_{int(datetime.now().timestamp())}.jpg"
                file_data = file.read()
                
                # Try multiple upload methods - Supabase might be misconfigured
                try:
                    # Method 1: Standard Supabase upload
                    result = supabase.storage.from_('uploads').upload(
                        path=filename, 
                        file=file_data, 
                        file_options={"content-type": "image/jpeg", "upsert": "true"}
                    )
                    url = supabase.storage.from_('uploads').get_public_url(filename)
                    print(f"Supabase upload success: {url}")
                    return url
                except Exception as upload_err:
                    print(f"Supabase upload failed: {upload_err}")
                    
                    # Method 2: Try manual Supabase API call with service key
                    try:
                        import urllib.request as _urlreq
                        import urllib.error as _urlerr
                        from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
                        
                        _auth_headers = {
                            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
                            'apikey': SUPABASE_SERVICE_KEY
                        }
                        
                        # Direct upload to Supabase storage
                        supa_path = f"uploads/{filename}"
                        _upload_req = _urlreq.Request(
                            f"{SUPABASE_URL}/storage/v1/object/{supa_path}",
                            method='POST',
                            data=file_data,
                            headers={**_auth_headers, 'Content-Type': 'image/jpeg', 'x-upsert': 'true'}
                        )
                        
                        with _urlreq.urlopen(_upload_req, timeout=15) as _resp:
                            if _resp.status in (200, 201):
                                url = f"{SUPABASE_URL}/storage/v1/object/public/uploads/{filename}"
                                print(f"Manual Supabase upload success: {url}")
                                return url
                    except Exception as manual_err:
                        print(f"Manual Supabase upload failed: {manual_err}")
                        
                    # Method 3: Save to local uploads folder as fallback
                    try:
                        import os
                        upload_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
                        os.makedirs(upload_dir, exist_ok=True)
                        
                        local_path = os.path.join(upload_dir, filename)
                        with open(local_path, 'wb') as f:
                            f.write(file_data)
                        
                        # Return relative URL for local storage
                        url = f"/static/uploads/{filename}"
                        print(f"Local upload fallback: {url}")
                        return url
                    except Exception as local_err:
                        print(f"Local upload fallback failed: {local_err}")
                        
                    # Method 4: Return placeholder URL to prevent complete failure
                    placeholder_url = f"/uploads/placeholder_{prefix}_{user_id}.jpg"
                    print(f"Upload failed, using placeholder: {placeholder_url}")
                    return placeholder_url
                    
            return None

        try:
            new_front = upload_img('license_front_file', 'license_front')
            if new_front: front_url = new_front
            
            new_back = upload_img('license_back_file', 'license_back')
            if new_back: back_url = new_back
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 413  # Payload too large
        except Exception as upload_err:
            print(f"Upload error: {upload_err}")
            # Continue without failing the entire request

        # Check if record exists
        cur.execute("SELECT id FROM license_details WHERE user_id = %s", (user_id,))
        exists = cur.fetchone()

        if exists:
            cur.execute("""
                UPDATE license_details SET
                    full_name=%s, date_of_birth=%s, license_number=%s, expiry_date=%s,
                    issuing_country_state=%s, license_class=%s, emergency_contact_name=%s,
                    emergency_contact_phone=%s, emergency_contact_relationship=%s,
                    license_front_url=%s, license_back_url=%s, updated_at=CURRENT_TIMESTAMP
                WHERE user_id=%s
            """, (full_name, date_of_birth, license_number, expiry_date, 
                  issuing_country_state, license_class, emergency_contact_name, 
                  emergency_contact_phone, emergency_contact_relationship, 
                  front_url, back_url, user_id))
        else:
            cur.execute("""
                INSERT INTO license_details (
                    user_id, full_name, date_of_birth, license_number, expiry_date,
                    issuing_country_state, license_class, emergency_contact_name,
                    emergency_contact_phone, emergency_contact_relationship,
                    license_front_url, license_back_url
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, full_name, date_of_birth, license_number, 
                  expiry_date, issuing_country_state, license_class, 
                  emergency_contact_name, emergency_contact_phone, 
                  emergency_contact_relationship, front_url, back_url))
            
        # Update user verification status and sync license info to users table
        cur.execute("""
            UPDATE users 
            SET is_verified = 1, 
                license_number = %s, 
                license_expiry = %s, 
                license_image_url = %s 
            WHERE id = %s
        """, (license_number, expiry_date, front_url, user_id))
        commit_db()

        # Notify admins (with error handling to prevent notification failures from breaking the main flow)
        try:
            cur.execute("SELECT full_name FROM users WHERE id = %s LIMIT 1", (user_id,))
            u = cur.fetchone()
            uname = (u['full_name'] if u else f'User #{user_id}')[:100]  # Limit name length
            notification_service.notify_admins_inapp(
                "License Details Updated",
                f"{uname} has submitted/updated their driver's license details and is awaiting verification.",
                'admin_license_upload',
                type='license',
                user_id=user_id
            )
        except Exception as notif_err:
            print(f"License details admin notification error: {notif_err}")
            # Don't fail the main request due to notification errors

        return jsonify({
            'message': 'License details saved successfully', 
            'is_verified': 1,
            'user_id': user_id
        }), 200
        
    except Exception as e:
        # Return minimal error to prevent large payloads
        error_msg = str(e)[:200]  # Limit error message length
        print(f"License details save error: {e}")
        return jsonify({'error': error_msg}), 500
    finally:
        if 'cur' in locals(): 
            cur.close()


# Restore admin FCM token function with unique function name to prevent Flask conflicts
@app.route('/admin/fcm-token', methods=['POST'])
def register_admin_device_fcm_token():
    """Register or update an admin's FCM device token for push notifications.
    Admin accounts are in the users table (role=admin/super_admin).
    """
    data = request.get_json(silent=True) or {}
    admin_id = data.get('admin_id')
    fcm_token = data.get('fcm_token')
    if not admin_id or not fcm_token:
        return jsonify({'error': 'admin_id and fcm_token are required'}), 400
    try:
        cur = get_cursor()
        # Ensure fcm_token column exists (auto-migrate if needed)
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS fcm_token TEXT")
            commit_db()
        except Exception:
            pass  # Column already exists or can't alter
        cur.execute(
            "UPDATE users SET fcm_token = %s WHERE id = %s AND role IN ('admin', 'super_admin')",
            (fcm_token, int(admin_id))
        )
        commit_db()
        print(f"[FCM] Admin {admin_id} token saved OK")
        return jsonify({'message': 'Admin FCM token registered'}), 200
    except Exception as e:
        print(f"[FCM] Admin FCM token save error: {e}")
        # Try fallback: upsert via separate statement
        try:
            cur2 = get_cursor()
            cur2.execute(
                "UPDATE users SET fcm_token = %s WHERE id = %s",
                (fcm_token, int(admin_id))
            )
            commit_db()
            cur2.close()
            print(f"[FCM] Admin {admin_id} token saved via fallback")
            return jsonify({'message': 'Admin FCM token registered (fallback)'}), 200
        except Exception as e2:
            print(f"[FCM] Admin FCM fallback error: {e2}")
            return jsonify({'error': str(e2)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/user/fcm-token', methods=['POST'])
def register_user_fcm_token():
    """Register or update a user's FCM device token for push notifications.
    Request body: { "user_id": int, "fcm_token": str }
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    fcm_token = data.get('fcm_token')
    if not user_id or not fcm_token:
        return jsonify({'error': 'user_id and fcm_token are required'}), 400
    try:
        cur = get_cursor()
        # Ensure fcm_token column exists (auto-migrate if needed)
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS fcm_token TEXT")
            commit_db()
        except Exception:
            pass  # Column already exists or can't alter
        cur.execute(
            "UPDATE users SET fcm_token = %s WHERE id = %s",
            (fcm_token, int(user_id))
        )
        commit_db()
        print(f"[FCM] User {user_id} token saved OK")
        return jsonify({'message': 'FCM token registered'}), 200
    except Exception as e:
        print(f"[FCM] User FCM token save error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


# ---------------------------------------------------------------------------
# In-App Notification Endpoints
# ---------------------------------------------------------------------------

@app.route('/debug/admin-fcm-check', methods=['GET'])
def debug_admin_fcm_check():
    """Debug: check admin FCM tokens and test push."""
    try:
        cur = get_cursor()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'admins' ORDER BY ordinal_position")
        columns = [r['column_name'] for r in cur.fetchall()]
        cur.execute("SELECT * FROM admins LIMIT 5")
        admins = [dict(r) for r in cur.fetchall()]
        for a in admins:
            a.pop('password', None)
            a.pop('password_hash', None)
        return jsonify({'columns': columns, 'admins': admins}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/debug/test-push', methods=['POST'])
def debug_test_push():
    """Debug: send a test push notification to an admin by admin_id (users.id)."""
    data = request.get_json(silent=True) or {}
    admin_id = data.get('admin_id')
    if not admin_id:
        return jsonify({'error': 'admin_id required'}), 400
    try:
        cur = get_cursor()
        cur.execute(
            "SELECT id, full_name, fcm_token FROM users WHERE id = %s AND role IN ('admin', 'super_admin')",
            (int(admin_id),)
        )
        admin = cur.fetchone()
        if not admin:
            return jsonify({'error': 'Admin not found in users table'}), 404
        if not admin.get('fcm_token'):
            return jsonify({'error': 'No FCM token registered for this admin', 'admin_id': admin_id}), 400
        from notifications import fcm_service
        ok = fcm_service.send_push(admin['fcm_token'], 'Test Notification', 'Push notifications are working!')
        return jsonify({'success': ok, 'admin_id': admin_id, 'token_prefix': admin['fcm_token'][:20] + '...'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/debug/test-user-push', methods=['POST'])
def debug_test_user_push():
    """
    Debug: send a test push notification to a customer by user_id.
    Body: { "user_id": int, "title": "optional", "body": "optional" }
    Also returns diagnostic info about token and FCM config.
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    try:
        import os
        cur = get_cursor()
        cur.execute("SELECT id, full_name, fcm_token FROM users WHERE id = %s", (int(user_id),))
        user = cur.fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        token = user.get('fcm_token')
        has_sa  = bool(os.environ.get('FIREBASE_SERVICE_ACCOUNT'))
        has_key = bool(os.environ.get('FCM_SERVER_KEY') or getattr(__import__('config'), 'FCM_SERVER_KEY', None))

        diag = {
            'user_id': user_id,
            'full_name': user.get('full_name'),
            'has_token': bool(token),
            'token_prefix': (token[:20] + '...') if token else None,
            'has_firebase_service_account_env': has_sa,
            'has_fcm_server_key': has_key,
        }

        if not token:
            return jsonify({'error': 'No FCM token registered for this user', 'diag': diag}), 400

        from notifications import fcm_service
        title = data.get('title', 'Autoride Test')
        body  = data.get('body',  'Push notifications are working! ??')
        ok = fcm_service.send_push(token, title, body)
        diag['push_sent'] = ok
        return jsonify({'success': ok, 'diag': diag}), 200 if ok else 500
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/debug/fcm-config', methods=['GET'])
def debug_fcm_config():
    """
    Check FCM configuration on the server without sending anything.
    Returns which credentials are present and whether the service account is valid.
    """
    import os
    sa_env = os.environ.get('FIREBASE_SERVICE_ACCOUNT', '')
    server_key = os.environ.get('FCM_SERVER_KEY', '')

    result = {
        'has_service_account_env': bool(sa_env),
        'service_account_length': len(sa_env),
        'has_server_key_env': bool(server_key),
        'server_key_prefix': (server_key[:10] + '...') if server_key else None,
    }

    # Try parsing the service account JSON
    if sa_env:
        try:
            import json
            sa = json.loads(sa_env)
            result['sa_project_id']    = sa.get('project_id', 'missing')
            result['sa_client_email']  = sa.get('client_email', 'missing')
            result['sa_has_private_key'] = bool(sa.get('private_key'))
            result['sa_valid_json']    = True
        except Exception as e:
            result['sa_valid_json']  = False
            result['sa_parse_error'] = str(e)
    else:
        # Check for local file fallback
        import os as _os
        sa_path = _os.path.join(_os.path.dirname(__file__), 'firebase-service-account.json')
        result['local_sa_file_exists'] = _os.path.exists(sa_path)

    # Try getting an access token (no push sent)
    try:
        from notifications import fcm_service
        token = fcm_service._get_access_token()
        result['can_get_access_token'] = bool(token)
    except Exception as e:
        result['can_get_access_token'] = False
        result['access_token_error']   = str(e)

    return jsonify(result), 200


@app.route('/debug/admins-schema-check', methods=['GET'])
def debug_admins_schema_check():
    """
    Diagnose why admins table appears empty.
    Forces SET search_path = public, then reports:
      - current DB, user, search_path
      - all schemas that contain an 'admins' table
      - row count in public.admins
      - up to 5 rows (passwords redacted)
    """
    try:
        cur = get_cursor()
        # Force the correct schema so we always hit the right table
        cur.execute("SET search_path = public")

        # Report connection identity
        cur.execute("SELECT current_database() AS db, current_user AS usr, current_setting('search_path') AS sp")
        conn_info = dict(cur.fetchone())

        # Find every schema that has an 'admins' table
        cur.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_name = 'admins'
            ORDER BY table_schema
        """)
        table_locations = [dict(r) for r in cur.fetchall()]

        # Count rows in public.admins explicitly
        cur.execute("SELECT COUNT(*) AS cnt FROM public.admins")
        row_count = cur.fetchone()['cnt']

        # Fetch up to 5 rows
        cur.execute("SELECT * FROM public.admins LIMIT 5")
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows:
            r.pop('password', None)
            r.pop('password_hash', None)

        # Also grab column list
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'admins'
            ORDER BY ordinal_position
        """)
        columns = [dict(r) for r in cur.fetchall()]

        return jsonify({
            'connection': conn_info,
            'admins_table_found_in_schemas': table_locations,
            'public_admins_row_count': row_count,
            'columns': columns,
            'sample_rows': rows,
        }), 200
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500
    finally:
        if 'cur' in locals():
            cur.close()


@app.route('/debug/fix-admin-fcm', methods=['POST'])
def debug_fix_admin_fcm():
    """
    Directly write an FCM token to the admins table in public schema.
    Bypasses any Vercel function-level caching of migration state.

    Body (JSON):
      { "admin_id": <int>,       -- use EITHER admin_id OR username
        "username":  <str>,
        "fcm_token": <str> }

    Returns the updated admin row (password redacted).
    """
    data = request.get_json(silent=True) or {}
    fcm_token = (data.get('fcm_token') or '').strip()
    admin_id  = data.get('admin_id')
    username  = (data.get('username') or '').strip()

    if not fcm_token:
        return jsonify({'error': 'fcm_token is required'}), 400
    if not admin_id and not username:
        return jsonify({'error': 'admin_id or username is required'}), 400

    try:
        cur = get_cursor()
        cur.execute("SET search_path = public")

        # Resolve admin_id from username if needed
        if not admin_id:
            cur.execute("SELECT id FROM public.admins WHERE username = %s", (username,))
            row = cur.fetchone()
            if not row:
                return jsonify({'error': f'Admin with username "{username}" not found in public.admins'}), 404
            admin_id = row['id']
        else:
            admin_id = int(admin_id)

        # Ensure fcm_token column exists (safe ALTER for older schemas)
        cur.execute("""
            ALTER TABLE public.admins
            ADD COLUMN IF NOT EXISTS fcm_token TEXT DEFAULT NULL
        """)
        commit_db()

        # Write the token
        cur.execute(
            "UPDATE public.admins SET fcm_token = %s WHERE id = %s",
            (fcm_token, admin_id)
        )
        rows_updated = cur.rowcount
        commit_db()

        if rows_updated == 0:
            return jsonify({'error': f'No admin found with id={admin_id} in public.admins'}), 404

        # Return updated row
        cur.execute("SELECT * FROM public.admins WHERE id = %s", (admin_id,))
        updated = dict(cur.fetchone())
        updated.pop('password', None)
        updated.pop('password_hash', None)

        return jsonify({
            'success': True,
            'rows_updated': rows_updated,
            'admin': updated,
        }), 200
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500
    finally:
        if 'cur' in locals():
            cur.close()


@app.route('/debug/booking-info/<int:booking_id>', methods=['GET'])
def debug_booking_info(booking_id):
    """Debug: show booking user_id and whether that user exists."""
    try:
        cur = get_cursor()
        cur.execute("SELECT id, user_id, status FROM bookings WHERE id = %s", (booking_id,))
        booking = cur.fetchone()
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        cur.execute("SELECT id, full_name FROM users WHERE id = %s", (booking['user_id'],))
        user = cur.fetchone()
        return jsonify({
            'booking_id': booking_id,
            'booking_user_id': booking['user_id'],
            'booking_status': booking['status'],
            'user_exists': user is not None,
            'user_name': user['full_name'] if user else None
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/debug/fix-old-admin-notifications', methods=['POST'])
def fix_old_admin_notifications():
    """One-time fix: assign old notifications (admin_id=null, user_id=null) to all admin users."""
    try:
        cur = get_cursor()
        # Get all admin user IDs
        cur.execute("SELECT id FROM users WHERE role IN ('admin', 'super_admin')")
        admin_ids = [r['id'] for r in cur.fetchall()]
        if not admin_ids:
            return jsonify({'error': 'No admin users found'}), 404

        # Get all orphaned admin notifications (admin_id null, user_id null, type starts with admin_)
        cur.execute("""
            SELECT id, title, message, type, created_at
            FROM notifications
            WHERE admin_id IS NULL AND user_id IS NULL
            AND type LIKE 'admin_%'
        """)
        orphaned = cur.fetchall()

        inserted = 0
        for notif in orphaned:
            for admin_id in admin_ids:
                cur.execute("""
                    INSERT INTO notifications (user_id, admin_id, title, message, type, created_at)
                    VALUES (NULL, %s, %s, %s, %s, %s)
                """, (admin_id, notif['title'], notif['message'], notif['type'], notif['created_at']))
                inserted += 1

        commit_db()
        return jsonify({
            'orphaned_found': len(orphaned),
            'admin_ids': admin_ids,
            'notifications_inserted': inserted,
            'message': f'Created {inserted} admin notification copies for {len(admin_ids)} admins'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/debug/admin-users-check', methods=['GET'])
def debug_admin_users_check():
    """Debug: check which users have admin/super_admin role."""
    try:
        cur = get_cursor()
        cur.execute("SELECT id, full_name, email, role FROM users WHERE role IN ('admin', 'super_admin') ORDER BY id")
        admins = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT COUNT(*) as total FROM notifications WHERE admin_id IS NOT NULL")
        admin_notif_count = cur.fetchone()['total']
        cur.execute("SELECT COUNT(*) as total FROM notifications WHERE admin_id IS NULL")
        user_notif_count = cur.fetchone()['total']
        return jsonify({
            'admin_users': admins,
            'admin_user_count': len(admins),
            'notifications_with_admin_id': admin_notif_count,
            'notifications_with_null_admin_id': user_notif_count
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/debug/notifications-check', methods=['GET'])
def debug_notifications_check():
    """Debug endpoint to check if notifications table exists and has rows."""
    try:
        cur = get_cursor()
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'notifications'
            ) as table_exists
        """)
        table_exists = cur.fetchone()['table_exists']
        if not table_exists:
            return jsonify({'table_exists': False, 'message': 'notifications table does not exist'}), 200
        cur.execute("SELECT COUNT(*) as total FROM notifications")
        total = cur.fetchone()['total']
        cur.execute("SELECT id, user_id, admin_id, title, type, created_at FROM notifications ORDER BY created_at DESC LIMIT 10")
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows:
            if r.get('created_at'):
                r['created_at'] = r['created_at'].isoformat()
        return jsonify({'table_exists': True, 'total': total, 'last_10': rows}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/debug/test-notification', methods=['GET', 'POST'])
def debug_test_notification():
    """Debug endpoint to directly test inserting a notification row."""
    try:
        # Get user_id from query param, body, or auto-detect from DB
        user_id = request.args.get('user_id') or (request.get_json(silent=True) or {}).get('user_id')
        cur = get_cursor()
        if not user_id:
            # Auto-detect: use the first user in the DB
            cur.execute("SELECT id FROM users ORDER BY id LIMIT 1")
            row = cur.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'No users found in database'}), 500
            user_id = row['id']
        else:
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': f'Invalid user_id: {user_id}'}), 400

        cur.execute(
            "INSERT INTO notifications (user_id, admin_id, title, message, type) VALUES (%s, NULL, %s, %s, %s) RETURNING id",
            (user_id, 'Test Notification', 'This is a test notification', 'test')
        )
        new_id = cur.fetchone()['id']
        commit_db()
        return jsonify({'success': True, 'notification_id': new_id, 'user_id': user_id}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/notifications', methods=['GET'])
def get_notifications():
    """Return all notifications for a customer ordered by created_at DESC.
    Query param: user_id (int, required)
    """
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'user_id must be an integer'}), 400
    try:
        cur = get_cursor()
        cur.execute(
            """
            SELECT id, title, message, type, is_read, created_at
            FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        rows = cur.fetchall()
        result = []
        for row in rows:
            entry = dict(row)
            if entry.get('created_at'):
                entry['created_at'] = entry['created_at'].isoformat()
            result.append(entry)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/notifications/read-all', methods=['POST'])
def mark_all_notifications_read():
    """Mark all notifications as read for a customer.
    Request body: { "user_id": int }
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    if user_id is None:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'user_id must be an integer'}), 400
    try:
        cur = get_cursor()
        cur.execute(
            "UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE",
            (user_id,)
        )
        updated = cur.rowcount
        commit_db()
        return jsonify({'updated': updated}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/notifications/<int:notif_id>/read', methods=['POST'])
def mark_notification_read(notif_id):
    """Mark a single notification as read.
    Request body: { "user_id": int }
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    if user_id is None:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'user_id must be an integer'}), 400
    try:
        cur = get_cursor()
        cur.execute(
            "SELECT id, user_id, title, message, type, is_read, created_at FROM notifications WHERE id = %s",
            (notif_id,)
        )
        notif = cur.fetchone()
        if not notif:
            return jsonify({'error': 'Notification not found'}), 404
        if notif['user_id'] != user_id:
            return jsonify({'error': 'Forbidden'}), 403
        cur.execute(
            "UPDATE notifications SET is_read = TRUE WHERE id = %s",
            (notif_id,)
        )
        commit_db()
        entry = dict(notif)
        entry['is_read'] = True
        if entry.get('created_at'):
            entry['created_at'] = entry['created_at'].isoformat()
        return jsonify(entry), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/admin/notifications', methods=['GET'])
def get_admin_notifications():
    """Return all notifications for an admin ordered by created_at DESC.
    Admin accounts are stored in the users table (role=admin/super_admin),
    so notifications are keyed by user_id.
    Query param: admin_id (int, required) - this is the users.id of the admin.
    Uses a dedicated connection to avoid shared connection state issues.
    """
    admin_id = request.args.get('admin_id')
    if not admin_id:
        return jsonify({'error': 'admin_id is required'}), 400
    try:
        admin_id = int(admin_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'admin_id must be an integer'}), 400
    try:
        import psycopg as _psycopg
        from config import SUPABASE_DB_URL as _SUPABASE_DB_URL
        from psycopg.rows import dict_row as _dict_row
        _conn = _psycopg.connect(conninfo=_SUPABASE_DB_URL)
        try:
            _cur = _conn.cursor(row_factory=_dict_row)
            _cur.execute(
                """
                SELECT id, title, message, type, is_read, created_at
                FROM notifications
                WHERE user_id = %s AND type LIKE 'admin\\_%%'
                ORDER BY created_at DESC
                """,
                (admin_id,)
            )
            rows = _cur.fetchall()
            result = []
            for row in rows:
                entry = dict(row)
                if entry.get('created_at'):
                    entry['created_at'] = entry['created_at'].isoformat()
                result.append(entry)
            return jsonify(result), 200
        finally:
            _conn.close()
    except Exception as e:
        print(f"GET ADMIN NOTIFICATIONS ERROR: {e}")
        return jsonify({'error': str(e)}), 500



@app.route('/admin/notifications/read-all', methods=['POST'])
def mark_all_admin_notifications_read():
    """Mark all notifications as read for an admin.
    Request body: { "admin_id": int }
    Uses a dedicated connection to avoid shared connection state issues.
    """
    data = request.get_json(silent=True) or {}
    admin_id = data.get('admin_id')
    if admin_id is None:
        return jsonify({'error': 'admin_id is required'}), 400
    try:
        admin_id = int(admin_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'admin_id must be an integer'}), 400
    try:
        import psycopg as _psycopg
        from config import SUPABASE_DB_URL as _SUPABASE_DB_URL
        _conn = _psycopg.connect(conninfo=_SUPABASE_DB_URL)
        try:
            _cur = _conn.cursor()
            _cur.execute(
                "UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND type LIKE 'admin_%%' AND is_read = FALSE",
                (admin_id,)
            )
            updated = _cur.rowcount
            _conn.commit()
            return jsonify({'updated': updated}), 200
        finally:
            _conn.close()
    except Exception as e:
        print(f"MARK ALL ADMIN NOTIFICATIONS READ ERROR: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/admin/notifications/<int:notif_id>/read', methods=['POST'])
def mark_admin_notification_read(notif_id):
    """Mark a single admin notification as read.
    Request body: { "admin_id": int }
    Uses a dedicated connection to avoid shared connection state issues.
    """
    data = request.get_json(silent=True) or {}
    admin_id = data.get('admin_id')
    if admin_id is None:
        return jsonify({'error': 'admin_id is required'}), 400
    try:
        admin_id = int(admin_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'admin_id must be an integer'}), 400
    try:
        import psycopg as _psycopg
        from config import SUPABASE_DB_URL as _SUPABASE_DB_URL
        from psycopg.rows import dict_row as _dict_row
        _conn = _psycopg.connect(conninfo=_SUPABASE_DB_URL)
        try:
            _cur = _conn.cursor(row_factory=_dict_row)
            _cur.execute(
                "SELECT id, user_id, title, message, type, is_read, created_at FROM notifications WHERE id = %s",
                (notif_id,)
            )
            notif = _cur.fetchone()
            if not notif:
                return jsonify({'error': 'Notification not found'}), 404
            if notif['user_id'] != admin_id:
                return jsonify({'error': 'Forbidden'}), 403
            _cur.execute(
                "UPDATE notifications SET is_read = TRUE WHERE id = %s",
                (notif_id,)
            )
            _conn.commit()
            entry = dict(notif)
            entry['is_read'] = True
            if entry.get('created_at'):
                entry['created_at'] = entry['created_at'].isoformat()
            return jsonify(entry), 200
        finally:
            _conn.close()
    except Exception as e:
        print(f"MARK ADMIN NOTIFICATION READ ERROR: {e}")
        return jsonify({'error': str(e)}), 500


# ?????????????????????????????????????????????
# CHAT ENDPOINTS
# ?????????????????????????????????????????????

@app.route('/users/search', methods=['GET'])
def users_search():
    """Search users by name or email. Used by admin chat to start new conversations."""
    q = (request.args.get('q') or '').strip()
    limit = min(int(request.args.get('limit', 10)), 50)
    if len(q) < 2:
        return jsonify([]), 200
    try:
        cur = get_cursor()
        cur.execute("""
            SELECT id, full_name, email FROM users
            WHERE full_name ILIKE %s OR email ILIKE %s
            ORDER BY full_name ASC
            LIMIT %s
        """, (f'%{q}%', f'%{q}%', limit))
        rows = cur.fetchall()
        return jsonify([dict(r) for r in rows]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/chat/send', methods=['POST'])
def chat_send():
    """Send a chat message. Works for both user?admin and admin?user."""
    import psycopg as _psycopg
    from config import SUPABASE_DB_URL as _DB_URL
    from psycopg.rows import dict_row as _dict_row
    data = request.get_json(silent=True) or {}
    sender_type   = data.get('sender_type')    # 'user' or 'admin'
    sender_id     = data.get('sender_id')
    receiver_type = data.get('receiver_type')  # 'user' or 'admin'
    receiver_id   = data.get('receiver_id')
    message       = (data.get('message') or '').strip()
    if not all([sender_type, sender_id, receiver_type, receiver_id, message]):
        return jsonify({'error': 'Missing required fields'}), 400
    conn = None
    try:
        conn = _psycopg.connect(conninfo=_DB_URL)
        cur  = conn.cursor(row_factory=_dict_row)
        cur.execute("""
            INSERT INTO chat_messages (sender_type, sender_id, receiver_type, receiver_id, message)
            VALUES (%s, %s, %s, %s, %s) RETURNING id, created_at
        """, (sender_type, int(sender_id), receiver_type, int(receiver_id), message))
        row = cur.fetchone()
        conn.commit()
        
        # Send push notification to receiver
        try:
            from notifications import fcm_service
            receiver_token = None
            sender_name = 'User'
            
            # Get receiver's FCM token and sender's name
            if receiver_type == 'admin':
                cur.execute("SELECT fcm_token, username FROM admins WHERE id = %s", (int(receiver_id),))
                receiver_row = cur.fetchone()
                if receiver_row:
                    receiver_token = receiver_row.get('fcm_token')
                # Get sender name (user)
                cur.execute("SELECT full_name FROM users WHERE id = %s", (int(sender_id),))
                sender_row = cur.fetchone()
                if sender_row:
                    sender_name = sender_row.get('full_name') or 'User'
            else:  # receiver is user
                cur.execute("SELECT fcm_token, full_name FROM users WHERE id = %s", (int(receiver_id),))
                receiver_row = cur.fetchone()
                if receiver_row:
                    receiver_token = receiver_row.get('fcm_token')
                # Get sender name (admin)
                cur.execute("SELECT username FROM admins WHERE id = %s", (int(sender_id),))
                sender_row = cur.fetchone()
                if sender_row:
                    sender_name = sender_row.get('username') or 'Support Team'
            
            # Send push notification if token exists
            if receiver_token:
                # Truncate message for notification
                notif_message = message[:100] + '...' if len(message) > 100 else message
                fcm_service.send_push(
                    receiver_token,
                    f'New message from {sender_name}',
                    notif_message
                )
        except Exception as notif_err:
            # Log but don't fail the request if notification fails
            print(f'Failed to send chat notification: {notif_err}')
        
        cur.close(); conn.close(); conn = None
        return jsonify({'id': row['id'], 'created_at': row['created_at'].isoformat()}), 201
    except Exception as e:
        if conn:
            try: conn.rollback()
            except: pass
            try: conn.close()
            except: pass
        return jsonify({'error': str(e)}), 500


@app.route('/chat/messages', methods=['GET'])
def chat_messages():
    """Get conversation between a user and an admin (paginated, newest last)."""
    user_id  = request.args.get('user_id')
    admin_id = request.args.get('admin_id')
    limit    = int(request.args.get('limit', 50))
    if not user_id or not admin_id:
        return jsonify({'error': 'user_id and admin_id required'}), 400
    try:
        cur = get_cursor()
        cur.execute("SET search_path = public")
        
        # Log the query parameters for debugging
        print(f"[CHAT_MESSAGES] user_id={user_id}, admin_id={admin_id}, limit={limit}")
        
        cur.execute("""
            SELECT id, sender_type, sender_id, receiver_type, receiver_id,
                   message, is_read, created_at
            FROM chat_messages
            WHERE (sender_type='user'  AND sender_id=%s   AND receiver_type='admin' AND receiver_id=%s)
               OR (sender_type='admin' AND sender_id=%s   AND receiver_type='user'  AND receiver_id=%s)
            ORDER BY created_at ASC
            LIMIT %s
        """, (int(user_id), int(admin_id), int(admin_id), int(user_id), limit))
        rows = cur.fetchall()
        
        print(f"[CHAT_MESSAGES] Found {len(rows)} messages")
        
        result = []
        for r in rows:
            d = dict(r)
            if d.get('created_at'): d['created_at'] = d['created_at'].isoformat()
            result.append(d)
            print(f"[CHAT_MESSAGES] Message: {d['sender_type']}({d['sender_id']}) -> {d['receiver_type']}({d['receiver_id']}): {d['message'][:30]}")
        
        return jsonify(result), 200
    except Exception as e:
        print(f"[CHAT_MESSAGES] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/debug/chat-messages-raw', methods=['GET'])
def debug_chat_messages_raw():
    """Debug: Show all chat messages in the database with full details."""
    try:
        cur = get_cursor()
        cur.execute("SET search_path = public")
        
        # Get all messages
        cur.execute("""
            SELECT id, sender_type, sender_id, receiver_type, receiver_id,
                   message, is_read, created_at
            FROM chat_messages
            ORDER BY created_at DESC
            LIMIT 50
        """)
        messages = [dict(r) for r in cur.fetchall()]
        for m in messages:
            if m.get('created_at'):
                m['created_at'] = m['created_at'].isoformat()
        
        # Get count
        cur.execute("SELECT COUNT(*) as cnt FROM chat_messages")
        total = cur.fetchone()['cnt']
        
        return jsonify({
            'total_messages': total,
            'recent_messages': messages
        }), 200
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/debug/chat-query-test', methods=['GET'])
def debug_chat_query_test():
    """Debug: Test the exact query used by /chat/messages endpoint."""
    user_id = request.args.get('user_id', '33')  # Default to user 33 from screenshot
    admin_id = request.args.get('admin_id', '20')  # Default to admin 20 from screenshot
    
    try:
        cur = get_cursor()
        cur.execute("SET search_path = public")
        
        # Run the exact same query as /chat/messages
        cur.execute("""
            SELECT id, sender_type, sender_id, receiver_type, receiver_id,
                   message, is_read, created_at
            FROM chat_messages
            WHERE (sender_type='user'  AND sender_id=%s   AND receiver_type='admin' AND receiver_id=%s)
               OR (sender_type='admin' AND sender_id=%s   AND receiver_type='user'  AND receiver_id=%s)
            ORDER BY created_at ASC
            LIMIT 100
        """, (int(user_id), int(admin_id), int(admin_id), int(user_id)))
        
        messages = [dict(r) for r in cur.fetchall()]
        for m in messages:
            if m.get('created_at'):
                m['created_at'] = m['created_at'].isoformat()
        
        return jsonify({
            'query_params': {
                'user_id': int(user_id),
                'admin_id': int(admin_id)
            },
            'message_count': len(messages),
            'messages': messages
        }), 200
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/chat/inbox', methods=['GET'])
def chat_inbox():
    """
    Get inbox for an admin: list of users who have chatted, with last message and unread count.
    Or for a user: list of admins they've chatted with.
    """
    viewer_type = request.args.get('viewer_type')  # 'admin' or 'user'
    viewer_id   = request.args.get('viewer_id')
    if not viewer_type or not viewer_id:
        return jsonify({'error': 'viewer_type and viewer_id required'}), 400
    try:
        cur = get_cursor()
        if viewer_type == 'admin':
            # Get all unique users this admin has chatted with, with latest message
            cur.execute("""
                SELECT
                    other_id,
                    last_message,
                    last_at,
                    (SELECT COUNT(*) FROM chat_messages
                     WHERE receiver_type='admin' AND receiver_id=%s
                       AND sender_type='user' AND sender_id=sub.other_id
                       AND is_read=FALSE) AS unread_count
                FROM (
                    SELECT DISTINCT ON (other_id)
                        CASE
                            WHEN sender_type='user' THEN sender_id
                            ELSE receiver_id
                        END AS other_id,
                        message AS last_message,
                        created_at AS last_at
                    FROM chat_messages
                    WHERE (sender_type='admin' AND sender_id=%s)
                       OR (receiver_type='admin' AND receiver_id=%s)
                    ORDER BY other_id,
                        CASE
                            WHEN sender_type='user' THEN sender_id
                            ELSE receiver_id
                        END,
                        created_at DESC
                ) sub
                ORDER BY last_at DESC
            """, (int(viewer_id), int(viewer_id), int(viewer_id)))
            rows = cur.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                if d.get('last_at'): d['last_at'] = d['last_at'].isoformat()
                cur.execute("SELECT full_name, email FROM users WHERE id=%s", (d['other_id'],))
                u = cur.fetchone()
                d['other_name'] = u['full_name'] if u else 'Unknown'
                d['other_email'] = u['email'] if u else ''
                result.append(d)
        else:
            # Get all unique admins this user has chatted with, with latest message
            cur.execute("""
                SELECT
                    other_id,
                    last_message,
                    last_at,
                    (SELECT COUNT(*) FROM chat_messages
                     WHERE receiver_type='user' AND receiver_id=%s
                       AND sender_type='admin' AND sender_id=sub.other_id
                       AND is_read=FALSE) AS unread_count
                FROM (
                    SELECT DISTINCT ON (other_id)
                        CASE
                            WHEN sender_type='admin' THEN sender_id
                            ELSE receiver_id
                        END AS other_id,
                        message AS last_message,
                        created_at AS last_at
                    FROM chat_messages
                    WHERE (sender_type='user' AND sender_id=%s)
                       OR (receiver_type='user' AND receiver_id=%s)
                    ORDER BY other_id,
                        CASE
                            WHEN sender_type='admin' THEN sender_id
                            ELSE receiver_id
                        END,
                        created_at DESC
                ) sub
                ORDER BY last_at DESC
            """, (int(viewer_id), int(viewer_id), int(viewer_id)))
            rows = cur.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                if d.get('last_at'): d['last_at'] = d['last_at'].isoformat()
                cur.execute("SELECT username FROM admins WHERE id=%s", (d['other_id'],))
                a = cur.fetchone()
                d['other_name'] = a['username'] if a else 'Admin'
                result.append(d)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/chat/mark-read', methods=['POST'])
def chat_mark_read():
    """Mark all messages in a conversation as read for the receiver."""
    data          = request.get_json(silent=True) or {}
    receiver_type = data.get('receiver_type')
    receiver_id   = data.get('receiver_id')
    sender_type   = data.get('sender_type')
    sender_id     = data.get('sender_id')
    if not all([receiver_type, receiver_id, sender_type, sender_id]):
        return jsonify({'error': 'Missing fields'}), 400
    try:
        cur = get_cursor()
        cur.execute("""
            UPDATE chat_messages SET is_read=TRUE
            WHERE receiver_type=%s AND receiver_id=%s
              AND sender_type=%s   AND sender_id=%s
              AND is_read=FALSE
        """, (receiver_type, int(receiver_id), sender_type, int(sender_id)))
        commit_db()
        return jsonify({'message': 'Marked as read'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/chat/admins', methods=['GET'])
def chat_list_admins():
    """Return list of active admins a customer can chat with.
    Falls back to all admins if is_active column doesn't exist yet.
    Also includes admins the user has already chatted with.
    """
    user_id = request.args.get('user_id')
    try:
        cur = get_cursor()
        # Check if is_active column exists
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='admins' AND column_name='is_active'
        """)
        has_col = cur.fetchone()
        if has_col:
            cur.execute("""
                SELECT id, username FROM admins
                WHERE is_active IS TRUE OR is_active IS NULL
                ORDER BY id ASC
            """)
        else:
            cur.execute("SELECT id, username FROM admins ORDER BY id ASC")
        rows = cur.fetchall()
        result = [dict(r) for r in rows]

        # If no admins found via is_active, fall back to admins from existing conversations
        if not result and user_id:
            try:
                cur.execute("""
                    SELECT DISTINCT
                        CASE WHEN sender_type='admin' THEN sender_id ELSE receiver_id END AS id
                    FROM chat_messages
                    WHERE (sender_type='user' AND sender_id=%s)
                       OR (receiver_type='user' AND receiver_id=%s)
                """, (int(user_id), int(user_id)))
                admin_ids = [r['id'] for r in cur.fetchall()]
                if admin_ids:
                    cur.execute("SELECT id, username FROM admins WHERE id = ANY(%s) ORDER BY id ASC", (admin_ids,))
                    result = [dict(r) for r in cur.fetchall()]
            except Exception:
                pass

        # Last resort: return first admin
        if not result:
            cur.execute("SELECT id, username FROM admins ORDER BY id ASC LIMIT 1")
            row = cur.fetchone()
            if row:
                result = [dict(row)]

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


# ── ADD-ONS CRUD ENDPOINTS ──
@app.route('/addons', methods=['GET'])
def get_addons():
    """Fetch all available rental addons from database."""
    try:
        cur = get_cursor()
        cur.execute("SELECT id, name, price_per_day, description FROM addons ORDER BY name ASC")
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d['price_per_day'] = float(d['price_per_day'])
            result.append(d)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/addons', methods=['POST'])
def create_addon():
    """Create a new rental addon. Admin only validation."""
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    price = data.get('price_per_day')
    desc = data.get('description', '').strip()
    admin_id = data.get('admin_id')

    if not name or price is None or not admin_id:
        return jsonify({'error': 'Name, price per day, and admin_id are required.'}), 400

    try:
        cur = get_cursor()
        cur.execute("SELECT id FROM users WHERE id = %s AND role = 'super_admin'", (admin_id,))
        if not cur.fetchone():
            return jsonify({'error': 'Unauthorized. Only Super Admin can manage add-ons.'}), 403

        cur.execute("""
            INSERT INTO addons (name, price_per_day, description)
            VALUES (%s, %s, %s) RETURNING id
        """, (name, float(price), desc))
        addon_id = cur.fetchone()['id']
        commit_db()
        return jsonify({'message': 'Addon created successfully', 'id': addon_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/addons/<int:addon_id>', methods=['PUT'])
def update_addon(addon_id):
    """Update an existing addon. Admin only validation."""
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    price = data.get('price_per_day')
    desc = data.get('description', '').strip()
    admin_id = data.get('admin_id')

    if not admin_id:
        return jsonify({'error': 'admin_id is required.'}), 400

    try:
        cur = get_cursor()
        cur.execute("SELECT id FROM users WHERE id = %s AND role = 'super_admin'", (admin_id,))
        if not cur.fetchone():
            return jsonify({'error': 'Unauthorized. Only Super Admin can manage add-ons.'}), 403

        updates = []
        params = []
        if name:
            updates.append("name = %s")
            params.append(name)
        if price is not None:
            updates.append("price_per_day = %s")
            params.append(float(price))
        if desc is not None:
            updates.append("description = %s")
            params.append(desc)

        if not updates:
            return jsonify({'error': 'No fields to update.'}), 400

        params.append(addon_id)
        cur.execute(f"UPDATE addons SET {', '.join(updates)} WHERE id = %s", tuple(params))
        commit_db()
        return jsonify({'message': 'Addon updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/addons/<int:addon_id>', methods=['DELETE'])
def delete_addon(addon_id):
    """Delete an addon. Admin only validation."""
    # Handle optional JSON or Query string arguments
    data = request.get_json(silent=True) or {}
    admin_id = data.get('admin_id') or request.args.get('admin_id')

    if not admin_id:
        return jsonify({'error': 'admin_id is required.'}), 400

    try:
        cur = get_cursor()
        cur.execute("SELECT id FROM users WHERE id = %s AND role = 'super_admin'", (admin_id,))
        if not cur.fetchone():
            return jsonify({'error': 'Unauthorized. Only Super Admin can manage add-ons.'}), 403

        cur.execute("DELETE FROM addons WHERE id = %s", (addon_id,))
        commit_db()
        return jsonify({'message': 'Addon deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/admin/expenses', methods=['POST'])
def record_expense():
    """Record a new vehicle expense. Accessible by admins and staff."""
    vehicle_id = request.form.get('vehicle_id')
    expense_type = request.form.get('expense_type')
    amount = request.form.get('amount')
    expense_date = request.form.get('expense_date')
    description = request.form.get('description', '')
    recorded_by = request.form.get('recorded_by')

    if not vehicle_id or not expense_type or not amount or not expense_date or not recorded_by:
        return jsonify({'error': 'Vehicle, type, amount, date, and recorded_by are required.'}), 400

    proof_image_url = None
    if 'proof_image' in request.files:
        file = request.files['proof_image']
        if file.filename != '':
            ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'jpg'
            filename = f"expense_{recorded_by}_{int(datetime.now().timestamp())}.{ext}"
            file_data = file.read()
            try:
                supabase.storage.from_('uploads').upload(
                    path=filename,
                    file=file_data,
                    file_options={"content-type": f"image/{ext}", "upsert": "true"}
                )
                proof_image_url = supabase.storage.from_('uploads').get_public_url(filename)
            except Exception as e:
                print(f"[record_expense] Supabase storage upload failed: {e}")
                return jsonify({'error': 'Failed to upload receipt image. Please try again.'}), 500

    try:
        cur = get_cursor()
        
        # Verify requester exists and is an admin/staff
        cur.execute("SELECT role FROM users WHERE id = %s", (recorded_by,))
        user_row = cur.fetchone()
        if not user_row or user_row['role'] not in ['admin', 'super_admin', 'superadmin', 'staff']:
            return jsonify({'error': 'Unauthorized. Only admin staff can record expenses.'}), 403

        cur.execute("""
            INSERT INTO vehicle_expenses (vehicle_id, expense_type, amount, expense_date, description, proof_image_url, recorded_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (int(vehicle_id), expense_type, float(amount), expense_date, description, proof_image_url, int(recorded_by)))
        
        expense_id = cur.fetchone()['id']
        commit_db()
        return jsonify({'message': 'Expense recorded successfully', 'id': expense_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/admin/expenses', methods=['GET'])
def get_expenses():
    """Retrieve filtered list of expenses."""
    admin_id = request.args.get('admin_id')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    vehicle_id = request.args.get('vehicle_id')

    try:
        cur = get_cursor()
        
        # Determine location lock if any
        location_filter = None
        if admin_id:
            cur.execute("SELECT role, assigned_location FROM users WHERE id = %s", (admin_id,))
            adm = cur.fetchone()
            if adm and adm['role'] == 'admin' and adm['assigned_location']:
                location_filter = adm['assigned_location']

        query = """
            SELECT e.*, v.brand, v.model, v.plate_number, u.full_name as recorder_name
            FROM vehicle_expenses e
            JOIN vehicles v ON e.vehicle_id = v.id
            LEFT JOIN users u ON e.recorded_by = u.id
            WHERE 1=1
        """
        params = []
        if location_filter:
            query += " AND v.location = %s"
            params.append(location_filter)
        if date_from:
            query += " AND e.expense_date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND e.expense_date <= %s"
            params.append(date_to)
        if vehicle_id and vehicle_id != 'all':
            query += " AND e.vehicle_id = %s"
            params.append(int(vehicle_id))

        query += " ORDER BY e.expense_date DESC"
        cur.execute(query, tuple(params))
        rows = cur.fetchall()

        expenses_list = []
        for r in rows:
            expenses_list.append({
                "id": r['id'],
                "vehicle_id": r['vehicle_id'],
                "brand": r['brand'],
                "model": r['model'],
                "plate_number": r['plate_number'],
                "expense_type": r['expense_type'],
                "amount": float(r['amount']),
                "expense_date": r['expense_date'].strftime('%Y-%m-%d'),
                "description": r['description'],
                "proof_image_url": r['proof_image_url'],
                "recorder_name": r['recorder_name'] or 'Unknown Admin',
                "recorded_by": r['recorded_by']
            })

        return jsonify(expenses_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/admin/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    """Delete an expense record. Super Admin only validation."""
    admin_id = request.args.get('admin_id')
    if not admin_id:
        return jsonify({'error': 'admin_id is required.'}), 400

    try:
        cur = get_cursor()
        cur.execute("SELECT role FROM users WHERE id = %s", (admin_id,))
        user_row = cur.fetchone()
        if not user_row or user_row['role'] not in ['super_admin', 'superadmin']:
            return jsonify({'error': 'Unauthorized. Only Super Admin can delete expense records.'}), 403

        cur.execute("DELETE FROM vehicle_expenses WHERE id = %s", (expense_id,))
        commit_db()
        return jsonify({'message': 'Expense record deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

