from flask import Flask, request, jsonify

from flask_cors import CORS

import typing

import os

from werkzeug.utils import secure_filename

from config import DEBUG, GOOGLE_CLIENT_ID, SEMAPHORE_API_KEY, SEMAPHORE_SENDER_NAME, SUPABASE_URL, SUPABASE_KEY

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



app = Flask(__name__, 

            static_folder='../frontend', 

            static_url_path='')

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

from utils.pdf_generator import generate_booking_pdf

import io

from flask import send_file



app.register_blueprint(booking_bp)

app.register_blueprint(payment_bp)

app.register_blueprint(report_bp)

app.register_blueprint(paymongo_bp)



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

        

        # 2. Ensure new keys exist with default values

        new_configs = [

            ('mileage_limit', '250', 'Daily mileage limit in kilometers'),

            ('long_term_discount_days', '7', 'Minimum days for long-term discount'),

            ('long_term_discount_percent', '10', 'Long-term discount percentage'),

        ]

        

        for key, val, desc in new_configs:

            cur.execute("""

                INSERT INTO settings (key, value, description) 

                VALUES (%s, %s, %s) 

                ON CONFLICT (key) DO NOTHING

            """, (key, val, desc))

            

        # 3. Force update the rental terms text

        terms_text = "Mileage Rule: 250 km per day. Rentals of 7 days or more get a 10% discount!"

        cur.execute("UPDATE settings SET value = %s WHERE key = 'rental_terms'", (terms_text,))

        

        commit_db()

        print("DEBUG: Settings Migration V2 Successful")

    except Exception as e:

        print(f"DEBUG: Settings Migration Failed: {e}")

    finally:

        if 'cur' in locals(): cur.close()



# Run migration on startup (Disabled for Vercel stability)

# with app.app_context():

#     migrate_settings_v2()



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

        print("DEBUG: Payment & Cancellation Migration Successful")

    except Exception as e:

        print(f"DEBUG: Payment & Cancellation Migration Failed: {e}")

    finally:

        if 'cur' in locals(): cur.close()



with app.app_context():

    migrate_payment_cancellation()



def migrate_sms_notification():

    """Adds SMS notification columns and tables: sms_opt_out on users, phone/is_active on admins, sms_logs table with indexes."""

    try:

        cur = get_cursor()

        # 1.1 users.sms_opt_out

        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS sms_opt_out BOOLEAN NOT NULL DEFAULT FALSE")

        # 1.2 admins.phone and admins.is_active

        cur.execute("ALTER TABLE admins ADD COLUMN IF NOT EXISTS phone VARCHAR(20)")

        cur.execute("ALTER TABLE admins ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE")

        # Ensure existing admins have is_active = TRUE (in case they were added before this column)

        cur.execute("UPDATE admins SET is_active = TRUE WHERE is_active IS NULL OR is_active = FALSE")

        # 1.3 sms_logs table

        cur.execute("""

            CREATE TABLE IF NOT EXISTS sms_logs (

                id                      SERIAL PRIMARY KEY,

                recipient_phone         TEXT NOT NULL,

                recipient_type          TEXT NOT NULL CHECK (recipient_type IN ('customer', 'admin')),

                recipient_id            INTEGER,

                message_body            TEXT NOT NULL,

                status                  TEXT NOT NULL CHECK (status IN ('sent', 'failed', 'retried')),

                semaphore_response_code INTEGER,

                error_message           TEXT,

                created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()

            )

        """)

        # 1.4 indexes

        cur.execute("CREATE INDEX IF NOT EXISTS idx_sms_logs_created_at ON sms_logs (created_at DESC)")

        cur.execute("CREATE INDEX IF NOT EXISTS idx_sms_logs_recipient_type ON sms_logs (recipient_type)")

        commit_db()

        print("DEBUG: SMS Notification Migration Successful")

    except Exception as e:

        print(f"DEBUG: SMS Notification Migration Failed: {e}")

    finally:

        if 'cur' in locals(): cur.close()



with app.app_context():

    migrate_sms_notification()



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

        print("DEBUG: Notifications Migration Successful")

    except Exception as e:

        print(f"DEBUG: Notifications Migration Failed: {e}")

    finally:

        if 'cur' in locals(): cur.close()



with app.app_context():

    migrate_notifications()

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
            print("DEBUG: Dropping old chat_messages table (chatbot schema) and recreating...")
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

        print("DEBUG: Chat Migration Successful")

    except Exception as e:

        print(f"DEBUG: Chat Migration Failed: {e}")

    finally:

        if 'cur' in locals(): cur.close()



with app.app_context():

    migrate_chat()

def migrate_fcm_tokens():
    """Adds fcm_token column to users and admins tables for push notifications."""
    try:
        cur = get_cursor()
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS fcm_token TEXT")
        cur.execute("ALTER TABLE admins ADD COLUMN IF NOT EXISTS fcm_token TEXT")
        commit_db()
        print("DEBUG: FCM Token Migration Successful")
    except Exception as e:
        print(f"DEBUG: FCM Token Migration Failed: {e}")
    finally:
        if 'cur' in locals(): cur.close()

with app.app_context():
    migrate_fcm_tokens()



@app.before_request

def log_request_info():

    print(f"DEBUG: Incoming {request.method} from {request.remote_addr}")

    print(f"DEBUG: Origin: {request.headers.get('Origin')}")



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

    finally:

        if 'cur' in locals(): cur.close()



from flask import send_from_directory



@app.route('/admin_app/<path:filename>')

def serve_admin_app(filename):

    return send_from_directory('../admin_app', filename)



@app.route('/admin_mobile/<path:filename>')

def serve_admin_mobile(filename):

    return send_from_directory('../admin_mobile/www', filename)



UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

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



from notifications import sms_service, notification_service, compose_booking_approved_sms, compose_booking_rejected_sms, compose_admin_cancel_sms, compose_pickup_sms, compose_completed_sms, compose_license_approved_sms, compose_license_rejected_sms, compose_customer_cancel_sms, compose_full_payment_sms, compose_downpayment_sms, compose_admin_payment_proof_sms, compose_modify_booking_sms, compose_split_request_sms, compose_split_paid_sms, compose_otp_sms



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

        print(f"DEBUG: Verification email sent to {email}")

    except Exception as e:

        print(f"DEBUG: SMTP Send Failed (Normal for Dev). Error: {str(e)}")



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

    # Build breakdown rows
    breakdown = (
        "<tr><td style='padding:10px 16px;font-size:13px;color:#6c757d;border-bottom:1px solid #dee2e6;width:50%;'>Base Rental</td>"
        "<td style='padding:10px 16px;font-size:13px;color:#212529;border-bottom:1px solid #dee2e6;text-align:right;'>PHP " + '{:,.2f}'.format(base_price) + "</td></tr>"
    )
    if addon_price > 0 and addons_raw and addons_raw != 'None':
        addon_list = [a.strip() for a in addons_raw.split(',') if a.strip()]
        for addon in addon_list:
            breakdown += (
                "<tr><td style='padding:8px 16px 8px 24px;font-size:12px;color:#6c757d;border-bottom:1px solid #dee2e6;'>+ " + addon + "</td>"
                "<td style='padding:8px 16px;font-size:12px;color:#212529;border-bottom:1px solid #dee2e6;text-align:right;'>PHP " + '{:,.2f}'.format(addon_price / max(1, len(addon_list))) + "</td></tr>"
            )
    if insurance_price > 0:
        breakdown += (
            "<tr><td style='padding:10px 16px;font-size:13px;color:#6c757d;border-bottom:1px solid #dee2e6;'>Insurance (" + insurance_text + ")</td>"
            "<td style='padding:10px 16px;font-size:13px;color:#212529;border-bottom:1px solid #dee2e6;text-align:right;'>PHP " + '{:,.2f}'.format(insurance_price) + "</td></tr>"
        )
    if discount_amount > 0:
        breakdown += (
            "<tr><td style='padding:10px 16px;font-size:13px;color:#2dc653;border-bottom:1px solid #dee2e6;'>Discount</td>"
            "<td style='padding:10px 16px;font-size:13px;color:#2dc653;border-bottom:1px solid #dee2e6;text-align:right;'>- PHP " + '{:,.2f}'.format(discount_amount) + "</td></tr>"
        )
    breakdown += (
        "<tr><td style='padding:12px 16px;font-size:14px;font-weight:bold;color:#212529;'>TOTAL</td>"
        "<td style='padding:12px 16px;font-size:14px;font-weight:bold;color:#e63946;text-align:right;'>PHP " + '{:,.2f}'.format(total_price) + "</td></tr>"
    )
    if payment_type == 'Downpayment' and balance_amount > 0:
        breakdown += (
            "<tr><td style='padding:10px 16px;font-size:13px;color:#e63946;border-top:2px solid #dee2e6;'>Paid Now (20%)</td>"
            "<td style='padding:10px 16px;font-size:13px;color:#e63946;border-top:2px solid #dee2e6;text-align:right;'>PHP " + '{:,.2f}'.format(amount_paid) + "</td></tr>"
            "<tr><td style='padding:10px 16px;font-size:13px;color:#6c757d;'>Remaining Balance</td>"
            "<td style='padding:10px 16px;font-size:13px;color:#6c757d;text-align:right;'>PHP " + '{:,.2f}'.format(balance_amount) + "</td></tr>"
        )

    html = (
        "<body style='margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;'>"
        "<table width='100%' cellpadding='0' cellspacing='0' style='background:#f4f4f4;padding:30px 0;'>"
        "<tr><td align='center'><table width='600' cellpadding='0' cellspacing='0' style='background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);'>"
        "<tr><td style='background:#e63946;padding:28px;text-align:center;'>"
        "<h1 style='color:#fff;margin:0;font-size:26px;'>Autoride</h1>"
        "<p style='color:rgba(255,255,255,0.85);margin:6px 0 0;font-size:13px;'>Your ride, your way</p></td></tr>"
        "<tr><td style='background:#2dc653;padding:12px;text-align:center;'>"
        "<p style='color:#fff;margin:0;font-size:14px;font-weight:bold;'>Booking Confirmed! - Booking #" + booking_id + "</p></td></tr>"
        "<tr><td style='padding:24px 28px 10px;'>"
        "<p style='font-size:15px;color:#212529;margin:0;'>Hello <strong>" + full_name + "</strong>,</p>"
        "<p style='font-size:13px;color:#6c757d;margin:8px 0 0;'>Thank you for choosing Autoride! Your payment has been received and your booking is confirmed.</p>"
        "</td></tr>"
        "<tr><td style='padding:16px 28px;'>"
        "<p style='font-size:13px;font-weight:bold;color:#212529;margin:0 0 10px;'>Booking Details</p>"
        "<table width='100%' cellpadding='0' cellspacing='0' style='background:#f8f9fa;border-radius:8px;overflow:hidden;'>"
        "<tr><td style='padding:10px 16px;font-size:13px;color:#6c757d;border-bottom:1px solid #dee2e6;width:40%;'>Vehicle</td>"
        "<td style='padding:10px 16px;font-size:13px;color:#212529;font-weight:bold;border-bottom:1px solid #dee2e6;'>" + brand + " " + model_name + "</td></tr>"
        "<tr><td style='padding:10px 16px;font-size:13px;color:#6c757d;border-bottom:1px solid #dee2e6;'>Rental Period</td>"
        "<td style='padding:10px 16px;font-size:13px;color:#212529;font-weight:bold;border-bottom:1px solid #dee2e6;'>" + start_date + " to " + end_date + "</td></tr>"
        "<tr><td style='padding:10px 16px;font-size:13px;color:#6c757d;border-bottom:1px solid #dee2e6;'>Insurance</td>"
        "<td style='padding:10px 16px;font-size:13px;color:#212529;border-bottom:1px solid #dee2e6;'>" + insurance_text + "</td></tr>"
        "<tr><td style='padding:10px 16px;font-size:13px;color:#6c757d;'>Add-ons</td>"
        "<td style='padding:10px 16px;font-size:13px;color:#212529;'>" + (addons_raw if addons_raw and addons_raw != 'None' else 'None') + "</td></tr>"
        "</table></td></tr>"
        "<tr><td style='padding:0 28px 16px;'>"
        "<p style='font-size:13px;font-weight:bold;color:#212529;margin:0 0 10px;'>Price Breakdown</p>"
        "<table width='100%' cellpadding='0' cellspacing='0' style='background:#f8f9fa;border-radius:8px;overflow:hidden;'>"
        + breakdown +
        "</table></td></tr>"
        "<tr><td style='padding:0 28px 16px;'>"
        "<p style='font-size:13px;font-weight:bold;color:#212529;margin:0 0 10px;'>Payment Details</p>"
        "<table width='100%' cellpadding='0' cellspacing='0' style='background:#f8f9fa;border-radius:8px;overflow:hidden;'>"
        "<tr><td style='padding:10px 16px;font-size:13px;color:#6c757d;border-bottom:1px solid #dee2e6;width:40%;'>Method</td>"
        "<td style='padding:10px 16px;font-size:13px;color:#212529;border-bottom:1px solid #dee2e6;'>" + method + "</td></tr>"
        "<tr><td style='padding:10px 16px;font-size:13px;color:#6c757d;'>Reference No.</td>"
        "<td style='padding:10px 16px;font-size:13px;color:#212529;font-weight:bold;'>" + ref_num + "</td></tr>"
        "</table></td></tr>"
        "<tr><td style='padding:0 28px 16px;text-align:center;'>"
        "<a href='" + receipt_url + "' style='display:inline-block;background:#e63946;color:#fff;text-decoration:none;padding:13px 28px;border-radius:8px;font-size:14px;font-weight:bold;'>Download PDF Receipt</a>"
        "</td></tr>"
        "<tr><td style='padding:0 28px 16px;'>"
        "<table width='100%' cellpadding='0' cellspacing='0' style='background:#fff3cd;border-radius:8px;border-left:4px solid #f4a261;'>"
        "<tr><td style='padding:14px;'>"
        "<p style='margin:0 0 6px;font-size:12px;font-weight:bold;color:#856404;'>Important Reminders</p>"
        "<p style='margin:3px 0;font-size:11px;color:#856404;'>- Bring 2 valid government-issued IDs upon pickup</p>"
        "<p style='margin:3px 0;font-size:11px;color:#856404;'>- Mileage limit: 250 km/day (excess: PHP 10/km)</p>"
        "<p style='margin:3px 0;font-size:11px;color:#856404;'>- Return vehicle with same fuel level as pickup</p>"
        "<p style='margin:3px 0;font-size:11px;color:#856404;'>- Late return penalty: PHP 500/hour</p>"
        "</td></tr></table></td></tr>"
        "<tr><td style='background:#f8f9fa;padding:18px 28px;text-align:center;border-top:1px solid #dee2e6;'>"
        "<p style='margin:0;font-size:12px;color:#6c757d;'>Safe travels! The Autoride Team</p>"
        "<p style='margin:4px 0 0;font-size:11px;color:#adb5bd;'>autoride-booking-system.vercel.app</p>"
        "</td></tr>"
        "</table></td></tr></table></body></html>"
    )

    print('RECEIPT EMAIL - TO: ' + email + ' BOOKING: #' + booking_id)
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = email
        msg.attach(MIMETextPart(html, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print('DEBUG: HTML receipt email sent to ' + email)
    except Exception as e:
        print('DEBUG: Receipt SMTP Failed. Error: ' + str(e))

@app.route("/")

def home():

    return "Autoride backend running"



@app.route('/register', methods=['POST'])

def register():

    # Handle both JSON and Multipart

    if request.is_json:

        data = request.json

        name = data.get('name')

        email = data.get('email')

        password = data.get('password')

    else:

        name = request.form.get('name')

        email = request.form.get('email')

        password = request.form.get('password')

    

    if not email or not is_gmail(email):

        return jsonify({"error": "Only @gmail.com emails are allowed for registration."}), 400

    

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

                filename = secure_filename(f"reg_license_{int(datetime.now().timestamp())}_{file.filename}")

                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                file.save(filepath)

                license_url = f"/uploads/{filename}"

                is_verified = 1 # Pending



        import random

        otp = str(random.randint(100000, 999999))

        temp_email_otps[email] = otp



        cur.execute("""

            INSERT INTO users(full_name, email, password, is_email_verified, is_verified, license_image_url, role)

            VALUES(%s, %s, %s, False, %s, %s, 'customer')

            RETURNING id

        """, (name, email, password, is_verified, license_url))

        

        user_id = cur.fetchone()['id']

        commit_db()

        send_verification_email(email, otp)



        return jsonify({

            "message": "Registration successful. Please verify your email.",

            "user_id": user_id,

            "verification_required": True

        }), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 400

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

        cur.execute("SELECT id, full_name, email, is_frozen, freeze_reason, is_email_verified, is_verified FROM users WHERE email=%s AND password=%s", (email, password))

        user = cur.fetchone()

        

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
        print(f"DEBUG verify-action: user_id={user_id} status={status} rows_updated={rows_updated}")

        # Verify before commit
        cur.execute("SELECT is_verified FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        print(f"DEBUG verify-action: pre-commit is_verified = {row}")

        conn.commit()
        print(f"DEBUG verify-action: committed successfully")

        # Verify after commit on same connection
        cur.execute("SELECT is_verified FROM users WHERE id = %s", (user_id,))
        row2 = cur.fetchone()
        print(f"DEBUG verify-action: post-commit is_verified = {row2}")

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
            sms_service.notify_customer(user_id, compose_license_approved_sms())
            notification_service.notify_user(
                user_id,
                "License Approved",
                "Your driver's license has been verified! You can now book vehicles on Autoride.",
                'license_approved'
            )
        elif status == 0:
            sms_service.notify_customer(user_id, compose_license_rejected_sms())
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

        cur.execute("SELECT is_verified, license_image_url FROM users WHERE id = %s", (user_id,))

        user = cur.fetchone()

        if not user: return jsonify({"error": "User not found"}), 404

        return jsonify(dict(user)), 200

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

        res = supabase.storage.from_('uploads').upload(

            path=filename,

            file=file_data,

            file_options={"content-type": "image/jpeg"}

        )

        

        # Get public URL

        url = supabase.storage.from_('uploads').get_public_url(filename)

        

        # is_verified = 1 means 'Pending Review'

        cur.execute("UPDATE users SET license_image_url = %s, is_verified = 1 WHERE id = %s", (url, user_id))

        commit_db()

        # Notify admins
        try:
            cur.execute("SELECT full_name FROM users WHERE id = %s", (user_id,))
            u = cur.fetchone()
            uname = u['full_name'] if u else f'User #{user_id}'
            notification_service.notify_admins_inapp(
                "License Uploaded for Review",
                f"{uname} has uploaded a driver's license and is awaiting verification.",
                'admin_license_upload'
            )
        except Exception as notif_err:
            print(f"License upload admin notification error: {notif_err}")

        return jsonify({"message": "License uploaded for verification", "url": url}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/admin/users', methods=['GET'])

@app.route('/admin/pending-verifications', methods=['GET'])

def admin_list_users():

    status = request.args.get('status')

    if 'pending-verifications' in request.path:

        status = 'pending'

        

    print(f"DEBUG: admin_list_users called with status={status} via path={request.path}")

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

        print(f"DEBUG: Found {len(result)} users matching criteria")

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
    data = request.get_json() or {}
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
    data = request.get_json() or {}
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    if not full_name:
        return jsonify({"error": "Full name is required"}), 400
    try:
        cur = get_cursor()
        cur.execute(
            "UPDATE users SET full_name = %s, phone = %s WHERE id = %s",
            (full_name, phone or None, user_id)
        )
        commit_db()
        return jsonify({"message": "User updated successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/users/<int:user_id>/loyalty', methods=['PUT'])
def admin_set_loyalty(user_id):
    """Set loyalty points for a user."""
    data = request.get_json() or {}
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
    data = request.get_json() or {}
    new_password = data.get('new_password', '').strip()
    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    import hashlib
    hashed = hashlib.sha256(new_password.encode()).hexdigest()
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



# Mock temporary store for OTPs

temp_otps = {}

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

            cur.execute("UPDATE users SET is_email_verified = True WHERE email = %s RETURNING id, full_name, is_driver", (email,))

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

            print(f"[GOOGLE_AUTH] Invalid token format")

            return jsonify({"error": "Invalid token format"}), 401

        

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

        

        cur = get_cursor()

        cur.execute("SELECT id, full_name, email, is_driver FROM users WHERE email=%s", (email,))

        user = cur.fetchone()

        

        if user:

            # User exists, link google_id if not present

            # UPDATE: Also update is_driver if requested

            cur.execute("UPDATE users SET google_id = %s, auth_provider = 'google', is_driver = CASE WHEN %s = 1 THEN 1 ELSE is_driver END WHERE email = %s", (google_id, is_driver, email))

            commit_db()

            

            # CHECK IF EMAIL IS ALREADY VERIFIED

            # Re-fetch with fresh data

            cur.execute("SELECT id, full_name, is_email_verified, is_driver FROM users WHERE email = %s", (email,))

            user_fresh = cur.fetchone()



            if user_fresh.get('is_email_verified') or google_email_verified:

                if google_email_verified and not user_fresh.get('is_email_verified'):

                    cur.execute("UPDATE users SET is_email_verified = True WHERE email = %s", (email,))

                    commit_db()

                

                # SKIP OTP - User is already verified!

                return jsonify({

                    "message": "login success",

                    "user": {

                        "id": user_fresh['id'],

                        "fullName": user_fresh['full_name'],

                        "email": email,

                        "isDriver": user_fresh.get('is_driver', 0),

                        "isVerified": 1

                    },

                    "verification_required": False

                }), 200



            # If not verified yet, REQUIRE OTP verification

            import random

            otp = str(random.randint(100000, 999999))

            temp_email_otps[email] = otp

            send_verification_email(email, otp)



            return jsonify({

                "message": "OTP sent to your Google email",

                "email": email,

                "verification_required": True

            }), 200

        else:

            # Create new user

            cur.execute("""

                INSERT INTO users (full_name, email, google_id, auth_provider, is_driver, is_email_verified, is_verified) 

                VALUES (%s, %s, %s, 'google', %s, %s, 0) RETURNING id

            """, (name, email, google_id, is_driver, google_email_verified))

            new_user_id = cur.fetchone()['id']

            commit_db()



            if google_email_verified:

                return jsonify({

                    "message": "login success",

                    "user": {

                        "id": new_user_id,

                        "fullName": name,

                        "email": email,

                        "isDriver": is_driver,

                        "isVerified": 1

                    },

                    "verification_required": False

                }), 201



            # REQUIRE OTP verification only if Google email not verified

            import random

            otp = str(random.randint(100000, 999999))

            temp_email_otps[email] = otp

            send_verification_email(email, otp)

            

            return jsonify({

                "message": "Registration successful. Please verify OTP.",

                "email": email,

                "verification_required": True

            }), 201

            

    except ValueError:

        # Invalid token

        return jsonify({"error": "Invalid Google token"}), 401

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/auth/request-otp', methods=['POST'])

def request_otp():

    data = request.json

    phone = data.get('phone')

    

    if not phone:

        return jsonify({"error": "Phone number is required"}), 400

        

    try:

        # Check if phone exists (for login)

        cur = get_cursor()

        cur.execute("SELECT id FROM users WHERE phone=%s", (phone,))

        user_row = cur.fetchone()

        if not user_row:

            return jsonify({"error": "No account found with this phone number. Please register normally first."}), 404

        user_id = user_row[0]

            

        import random

        otp = str(random.randint(100000, 999999))

        temp_otps[phone] = otp

        

        # Ensure number is in 11-digit local format for Semaphore (09XXXXXXXXX)

        formatted_phone = phone

        if phone.startswith('+63'):

            formatted_phone = '0' + phone[3:]

        elif not phone.startswith('0'):

            formatted_phone = '0' + phone

        

        # Send OTP via SMS_Service abstraction

        sent = sms_service.notify_phone(formatted_phone, compose_otp_sms(otp), 'customer', user_id)

        

        if not sent:

            return jsonify({"error": "Failed to send OTP. Please try again."}), 500

        

        return jsonify({"message": "OTP sent successfully to your mobile phone"}), 200

            

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



@app.route('/auth/verify-otp', methods=['POST'])

def verify_otp():

    data = request.json

    phone = data.get('phone')

    otp = data.get('otp')

    

    if temp_otps.get(phone) == str(otp):

        # Successful verification

        try:

            cur = get_cursor()

            cur.execute("SELECT id, full_name FROM users WHERE phone=%s", (phone,))

            user = cur.fetchone()

            temp_otps.pop(phone, None) # Clear the OTP

            if user:

                return jsonify({"message": "login success", "user_id": user['id'], "full_name": user['full_name']}), 200

            else:

                return jsonify({"error": "User not found during OTP verification."}), 404

        except Exception as e:

            return jsonify({"error": str(e)}), 500

        finally:

            if 'cur' in locals():

                cur.close()

    else:

        return jsonify({"error": "Invalid or expired OTP"}), 401





@app.route('/coupons/verify', methods=['POST'])

def verify_coupon():

    data = request.json

    code = data.get('code')

    if not code:

        return jsonify({"error": "Coupon code is required"}), 400

    

    try:

        cur = get_cursor()

        cur.execute("""

            SELECT id, code, discount_percent, expiry_date, usage_limit, times_used, is_active 

            FROM coupons WHERE code = %s AND is_active = TRUE

        """, (code,))

        coupon = cur.fetchone()

        

        if not coupon:

            return jsonify({"error": "Invalid or inactive coupon code"}), 404

        

        # Check Expiry

        from datetime import date

        if coupon['expiry_date'] < date.today():

            return jsonify({"error": "Coupon has expired"}), 400

            

        # Check Usage Limit

        if coupon['usage_limit'] and coupon['times_used'] >= coupon['usage_limit']:

            return jsonify({"error": "Coupon usage limit reached"}), 400

            

        return jsonify({

            "message": "Coupon applied!",

            "coupon_id": coupon['id'],

            "discount_percent": coupon['discount_percent']

        }), 200

        

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals():

            cur.close()



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

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        file.save(filepath)

        url = f"/uploads/{filename}"

        

        cur.execute("""

            UPDATE bookings 

            SET payment_status = 'Refunded', 

                refund_proof_url = %s 

            WHERE id = %s

        """, (url, booking_id))

        

        # Log activity

        cur.execute("SELECT username FROM admins WHERE id = %s", (admin_id,))

        admin = cur.fetchone()

        admin_name = admin['username'] if admin else f"Admin {admin_id}"

        

        log_activity(admin_id, admin_name, "Uploaded refund proof", "booking", booking_id, f"Marked as Refunded. Receipt: {url}")

        

        commit_db()

        return jsonify({"message": "Refund proof uploaded and booking updated to Refunded.", "url": url}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



# Legacy vehicle routes removed to resolve duplicate endpoint conflicts.



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

    print(f"DEBUG: Attempting to delete vehicle image with ID: {image_id}")

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

                WHERE status IN ('Confirmed', 'Pending', 'Picked Up')

                AND (%s <= end_date AND %s >= start_date)

            )

            LIMIT 1

        """, (category['brand'], category['model'], start_date, end_date))

        

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



        # New fields

        addons = ",".join(data.get('addons', []))

        base_price = data.get('base_price')

        addon_price = data.get('addon_price')

        tax_amount = data.get('tax_amount')

        total_price = data.get('total_price')

        # Ensure time columns exist

        try:

            cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS pickup_time VARCHAR(5) DEFAULT '06:00'")

            cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS return_time VARCHAR(5) DEFAULT '06:00'")

            commit_db()

        except Exception:

            pass



        cur.execute("""

            INSERT INTO bookings (

                user_id, vehicle_id, start_date, end_date, pickup_location, rental_type, addons, 

                base_price, addon_price, tax_amount, total_price, status,

                pickup_province, pickup_municipality, pickup_barangay,

                return_province, return_municipality, return_barangay,

                pickup_time, return_time

            )

            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending', %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id

        """, (user_id, final_vehicle_id, start_date, end_date, pickup_location, rental_type, addons, 

              base_price, addon_price, tax_amount, total_price,

              pickup_province, pickup_municipality, pickup_barangay,

              return_province, return_municipality, return_barangay,

              pickup_time, return_time))

        

        booking_id = cur.fetchone()['id']

        

        print(f"DEBUG: Booking created ID={booking_id} for Vehicle ID={vehicle_id}")

        

        # Update vehicle status to 'Booked'

        cur.execute("UPDATE vehicles SET status = 'Booked' WHERE id = %s", (final_vehicle_id,))

        print(f"DEBUG: Vehicle {final_vehicle_id} status updated to Booked")

        

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

        

        print(f"DEBUG: Payment received for Booking ID={booking_id}")

        

        # Ensure vehicle status is 'Booked'

        cur.execute("UPDATE vehicles SET status='Booked' WHERE id=(SELECT vehicle_id FROM bookings WHERE id=%s)", (booking_id,))

        print(f"DEBUG: Vehicle linked to booking {booking_id} status ensured to Booked")

        

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

            # Send SMS notifications after successful commit
            try:
                user_id_sms = details_dict.get('user_id') or (booking_row['user_id'] if booking_row else None)
                if not user_id_sms:
                    cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))
                    bk_row = cur.fetchone()
                    user_id_sms = bk_row['user_id'] if bk_row else None
                if user_id_sms:
                    payment_type = details_dict.get('payment_type', 'Full')
                    if payment_type == 'Downpayment':
                        sms_msg = compose_downpayment_sms(
                            booking_id,
                            float(details_dict.get('amount_paid') or amount or 0),
                            float(details_dict.get('balance_amount') or 0),
                            details_dict.get('reference_number', reference_number),
                        )
                    else:
                        sms_msg = compose_full_payment_sms(
                            booking_id,
                            float(details_dict.get('amount_paid') or amount or 0),
                            details_dict.get('method', method or ''),
                            details_dict.get('reference_number', reference_number),
                        )
                    sms_service.notify_customer(user_id_sms, sms_msg)
                    notification_service.notify_user(
                        user_id_sms,
                        "Payment Confirmed",
                        f"Payment proof received for booking #{booking_id}. Amount: PHP {float(amount or 0)}.",
                        'payment_confirmed'
                    )
                customer_name = details_dict.get('full_name', 'Customer')
                sms_service.notify_admins(
                    compose_admin_payment_proof_sms(booking_id, customer_name, float(amount or 0))
                )
                notification_service.notify_admins_inapp(
                    "Payment Proof Uploaded",
                    f"Payment proof uploaded for booking #{booking_id} by {customer_name}. Amount: PHP {float(amount or 0)}.",
                    'admin_payment_proof'
                )
            except Exception as sms_err:
                print(f"ERROR SENDING LEGACY PAYMENT SMS: {sms_err}")

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
        # Send admin payment proof alert when receipt details are unavailable
        try:
            cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))
            bk_row = cur.fetchone()
            if bk_row:
                sms_service.notify_customer(
                    bk_row['user_id'],
                    compose_full_payment_sms(booking_id, float(amount or 0), method or '', reference_number)
                )
                notification_service.notify_user(
                    bk_row['user_id'],
                    "Payment Confirmed",
                    f"Payment proof received for booking #{booking_id}. Amount: PHP {float(amount or 0)}.",
                    'payment_confirmed'
                )
            sms_service.notify_admins(
                compose_admin_payment_proof_sms(booking_id, 'Customer', float(amount or 0))
            )
            notification_service.notify_admins_inapp(
                "Payment Proof Uploaded",
                f"Payment proof uploaded for booking #{booking_id} by Customer. Amount: PHP {float(amount or 0)}.",
                'admin_payment_proof'
            )
        except Exception as sms_err:
            print(f"ERROR SENDING LEGACY PAYMENT SMS: {sms_err}")
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

        cur = get_cursor()

        # Fetch bookings with vehicle info - Use LEFT JOIN to ensure booking shows even if vehicle data has issues

        query = """

            SELECT b.*, v.brand, v.model, v.plate_number, v.vehicle_image

            FROM bookings b

            LEFT JOIN vehicles v ON b.vehicle_id = v.id

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



@app.route('/update-profile', methods=['POST'])

def update_profile():

    try:

        user_id = request.form.get('user_id')

        full_name = request.form.get('full_name')

        phone = request.form.get('phone')

        

        cur = get_cursor()

        

        if 'profile_picture' in request.files:

            file = request.files['profile_picture']

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

                    print(f"DEBUG: Profile picture uploaded to Supabase: {public_url}")

                except Exception as storage_err:

                    print(f"STORAGE ERROR: {str(storage_err)}")

                    # Fallback to local filename just in case, or handle error

                    raise storage_err



        cur.execute("UPDATE users SET full_name=%s, phone=%s WHERE id=%s", (full_name, phone, user_id))

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





@app.route('/cancel-booking', methods=['POST'])

def cancel_booking():

    data = request.json

    booking_id = data.get('booking_id')

    try:

        cur = get_cursor()

        # Only allow cancellation if pending

        cur.execute("SELECT status, user_id FROM bookings WHERE id=%s", (booking_id,))

        bk = cur.fetchone()

        if bk and bk['status'] == 'Pending':

            cur.execute("UPDATE bookings SET status='Cancelled' WHERE id=%s", (booking_id,))

            

            # Reset vehicle status to 'Available'

            cur.execute("UPDATE vehicles SET status='Available' WHERE id=(SELECT vehicle_id FROM bookings WHERE id=%s)", (booking_id,))

            

            commit_db()

            

            # Send SMS notification

            reason = (data or {}).get('reason', 'No reason provided')

            sms_service.notify_customer(

                bk['user_id'],

                compose_customer_cancel_sms(booking_id, reason)

            )

            notification_service.notify_user(

                bk['user_id'],

                "Booking Cancelled",

                f"Your booking #{booking_id} has been cancelled. Reason: {reason}.",

                'booking_cancelled'

            )

            

            return jsonify({"message": "Booking cancelled"}), 200

        else:

            return jsonify({"error": "Cannot cancel this booking"}), 400

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

            SELECT b.total_price, v.daily_rate, b.status 

            FROM bookings b 

            JOIN vehicles v ON b.vehicle_id = v.id 

            WHERE b.id = %s

        """, (booking_id,))

        bk = cur.fetchone()

        

        if not bk or bk['status'] not in ['Pending', 'Confirmed']:

            return jsonify({"error": "Booking cannot be modified"}), 400

            

        rate = float(bk['daily_rate'])

        # Simple days calc (reusing logic from frontend usually, but here for total_price update)

        from datetime import datetime

        d1 = datetime.strptime(new_start, "%Y-%m-%d")

        d2 = datetime.strptime(new_end, "%Y-%m-%d")

        days = (d2 - d1).days + 1

        

        if days <= 0:

            return jsonify({"error": "Invalid dates"}), 400

            

        new_total = days * rate

        # Apply 10% discount if days >= 7

        if days >= 7:

            new_total *= 0.90

        # Preview mode - return new total without saving
        if preview:
            return jsonify({"new_total": float(f"{new_total:.2f}")}), 200

        cur.execute("""

            UPDATE bookings 

            SET start_date = %s, end_date = %s, total_price = %s 

            WHERE id = %s

        """, (new_start, new_end, new_total, booking_id))

        

        commit_db()

        # Send SMS notification to customer
        try:
            cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))
            bk_row = cur.fetchone()
            if bk_row:
                sms_service.notify_customer(
                    bk_row['user_id'],
                    compose_modify_booking_sms(booking_id, new_start, new_end, round(new_total, 2))
                )
                notification_service.notify_user(
                    bk_row['user_id'],
                    "Booking Updated",
                    f"Your booking #{booking_id} dates have been updated: {new_start} to {new_end}. New total: PHP {round(new_total, 2)}.",
                    'booking_modified'
                )
        except Exception as sms_err:
            print(f"ERROR SENDING MODIFY BOOKING SMS: {sms_err}")

        return jsonify({"message": "Booking modified", "new_total": float(f"{new_total:.2f}")}), 200

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
                sms_service.notify_customer(
                    partner_row['id'],
                    compose_split_request_sms(booking_id, initiator_name, float(amount))
                )
                notification_service.notify_user(
                    partner_row['id'],
                    "Split Payment Request",
                    f"{initiator_name} has requested a split payment for booking #{booking_id}. Your share: PHP {float(amount)}.",
                    'split_request'
                )
        except Exception as sms_err:
            print(f"ERROR SENDING SPLIT REQUEST SMS: {sms_err}")

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
                    sms_service.notify_customer(
                        bk_row['user_id'],
                        compose_split_paid_sms(b_id['booking_id'], float(sp_row['amount']))
                    )
                    notification_service.notify_user(
                        bk_row['user_id'],
                        "Split Payment Received",
                        f"Your split payment partner has paid PHP {float(sp_row['amount'])} for booking #{b_id['booking_id']}.",
                        'split_paid'
                    )
        except Exception as sms_err:
            print(f"ERROR SENDING SPLIT PAID SMS: {sms_err}")

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

        cur = get_cursor()

        

        # Determine location filter

        location_filter = None

        if admin_id:

            cur.execute("SELECT role, assigned_location FROM users WHERE id = %s", (admin_id,))

            admin = cur.fetchone()

            if admin and admin['role'] == 'admin' and admin['assigned_location']:

                location_filter = admin['assigned_location']



        query = """

            SELECT b.id, u.full_name AS customer_name,

                   CONCAT(v.brand, ' ', v.model, ' (', v.plate_number, ')') AS car,

                   b.start_date, b.end_date, b.total_price, b.status,

                   b.payment_status,

                   b.pickup_location, b.rental_type, b.addons,

                   b.driver_id, d.full_name AS driver_name

            FROM bookings b

            JOIN users u ON b.user_id = u.id

            JOIN vehicles v ON b.vehicle_id = v.id

            LEFT JOIN drivers d ON b.driver_id = d.id

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
        sort_clause = "b.updated_at DESC"  # Default: cancellation date descending
        if sort_by == 'cancellation_date_asc':
            sort_clause = "b.updated_at ASC"
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
                   b.updated_at AS cancellation_date,
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
            sms_service.notify_customer(
                b_data['user_id'],
                compose_booking_approved_sms(booking_id, b_data['brand'], b_data['model'], b_data['start_date'])
            )
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



@app.route('/inspections/submit', methods=['POST'])

def submit_inspection():

    """Submit a vehicle inspection (pickup or return)."""

    try:

        # Handle Multipart Form (for images)

        booking_id = request.form.get('booking_id')

        inspection_type = request.form.get('inspection_type') # 'pickup' or 'return'

        mileage = request.form.get('mileage')

        fuel_level = request.form.get('fuel_level')

        notes = request.form.get('notes')

        inspector_id = request.form.get('inspector_id')

        

        if not booking_id or not inspection_type:

            return jsonify({"error": "Missing required fields"}), 400



        photo_urls = []

        # Handle multiple photo uploads

        if 'photos' in request.files:

            files = request.files.getlist('photos')

            for file in files:

                if file.filename != '':

                    filename = f"inspect_{booking_id}_{inspection_type}_{int(datetime.now().timestamp())}_{secure_filename(file.filename)}"

                    

                    # Upload to Supabase Storage

                    file_data = file.read()

                    supabase.storage.from_('uploads').upload(

                        path=filename,

                        file=file_data,

                        file_options={"content-type": file.content_type}

                    )

                    url = supabase.storage.from_('uploads').get_public_url(filename)

                    photo_urls.append(url)



        cur = get_cursor()

        

        # Save to database

        import json

        cur.execute("""

            INSERT INTO vehicle_inspections (booking_id, inspection_type, photos, mileage, fuel_level, notes, inspector_id)

            VALUES (%s, %s, %s, %s, %s, %s, %s)

            RETURNING id

        """, (booking_id, inspection_type, json.dumps(photo_urls), mileage, fuel_level, notes, inspector_id))

        

        inspection_id = cur.fetchone()['id']

        

        # Auto-update booking and vehicle status based on inspection type

        if inspection_type == 'pickup':

            # Mark booking as Picked Up and vehicle as Rented

            cur.execute("UPDATE bookings SET status = 'Picked Up' WHERE id = %s", (booking_id,))

            cur.execute("UPDATE vehicles SET status = 'Rented' WHERE id = (SELECT vehicle_id FROM bookings WHERE id = %s)", (booking_id,))

        elif inspection_type == 'return':

            # Mark booking as Completed and vehicle as Available

            cur.execute("UPDATE bookings SET status = 'Completed' WHERE id = %s", (booking_id,))

            cur.execute("UPDATE vehicles SET status = 'Available' WHERE id = (SELECT vehicle_id FROM bookings WHERE id = %s)", (booking_id,))



        commit_db()

        return jsonify({"message": "Inspection submitted successfully", "id": inspection_id}), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/inspections/<int:booking_id>', methods=['GET'])

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

    """Allow a user to cancel their own booking."""

    try:

        data = request.json

        booking_id = data.get('booking_id')

        user_id = data.get('user_id') # Optional but good for validation

        

        cur = get_cursor()

        # Verify ownership and status

        cur.execute("SELECT user_id, status, vehicle_id FROM bookings WHERE id=%s", (booking_id,))

        booking = cur.fetchone()

        

        if not booking:

            return jsonify({"error": "Booking not found"}), 404

            

        # Security: Only the owner (or admin) can cancel

        # If user_id is provided, verify it matches

        if user_id and int(booking['user_id']) != int(user_id):

            return jsonify({"error": "Unauthorized. You can only cancel your own bookings."}), 403



        if booking['status'] not in ['Pending', 'Confirmed']:

            return jsonify({"error": f"Cannot cancel a booking that is '{booking['status']}'"}), 400



        # Determine if refund is needed

        # If status was 'Confirmed' (Paid), set to Refund Pending

        # If it was 'Pending' (Unpaid), set to N/A or Cancelled

        new_payment_status = 'Refund Pending' if booking['status'] == 'Confirmed' else 'Cancelled'



        # Update booking status

        cur.execute("""

            UPDATE bookings 

            SET status='Cancelled', payment_status=%s 

            WHERE id=%s

        """, (new_payment_status, booking_id))

        

        # Reset vehicle status to 'Available'

        if booking['vehicle_id']:

            cur.execute("UPDATE vehicles SET status='Available' WHERE id=%s", (booking['vehicle_id'],))

        

        commit_db()

        

        # Send SMS notification

        reason = (request.json or {}).get('reason', 'No reason provided')

        sms_service.notify_customer(

            booking['user_id'],

            compose_customer_cancel_sms(booking_id, reason)

        )



        return jsonify({"message": "Booking cancelled successfully"}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

    finally:

        if 'cur' in locals(): cur.close()



@app.route('/bookings/<int:booking_id>/reject', methods=['PUT'])

def reject_booking(booking_id):

    """Reject a pending booking."""

    try:

        cur = get_cursor()

        cur.execute("SELECT status, vehicle_id, user_id FROM bookings WHERE id=%s", (booking_id,))

        row = cur.fetchone()

        

        if not row:

            return jsonify({"error": "Booking not found"}), 404

        if row['status'] != 'Pending':

            return jsonify({"error": f"Cannot reject a booking with status '{row['status']}'"}), 400

            

        cur.execute("UPDATE bookings SET status='Rejected' WHERE id=%s", (booking_id,))

        commit_db()

        

        # Send SMS notification

        sms_service.notify_customer(

            row['user_id'],

            compose_booking_rejected_sms(booking_id)

        )

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



@app.route('/bookings/<int:booking_id>/cancel', methods=['PUT'])

def admin_cancel_booking(booking_id):

    """Cancel an approved/confirmed booking and trigger refund if needed."""

    try:

        cur = get_cursor()

        cur.execute("SELECT status, payment_status, vehicle_id, user_id FROM bookings WHERE id=%s", (booking_id,))

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

            SET status='Cancelled', payment_status=%s 

            WHERE id=%s

        """, (new_payment_status, booking_id))

        

        # Reset vehicle status to 'Available'

        if booking['vehicle_id']:

            cur.execute("UPDATE vehicles SET status='Available' WHERE id=%s", (booking['vehicle_id'],))

        

        commit_db()



        # Send SMS notification

        reason = (request.json or {}).get('reason', 'No reason provided')

        sms_service.notify_customer(

            booking['user_id'],

            compose_admin_cancel_sms(booking_id, reason)

        )

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
            print(f"DEBUG: notification inserted for user_id={booking['user_id']}, booking_id={booking_id}")
        except Exception as notif_err:
            notif_error = str(notif_err)
            print(f"DEBUG: notification insert failed for user_id={booking['user_id']}: {notif_err}")

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

        

        # Send SMS notification

        cur.execute(

            """SELECT b.user_id, v.brand, v.model, b.end_date

               FROM bookings b

               JOIN vehicles v ON b.vehicle_id = v.id

               WHERE b.id = %s""",

            (booking_id,)

        )

        b_data = cur.fetchone()

        if b_data:

            sms_service.notify_customer(

                b_data['user_id'],

                compose_pickup_sms(booking_id, b_data['brand'], b_data['model'], b_data['end_date'])

            )

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

        cur.execute("UPDATE bookings SET status='Completed' WHERE id=%s", (booking_id,))

        

        # Reset vehicle status to 'Available'

        cur.execute("UPDATE vehicles SET status='Available' WHERE id=(SELECT vehicle_id FROM bookings WHERE id=%s)", (booking_id,))

        

        commit_db()

        

        # Send SMS notification

        cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))

        b_data = cur.fetchone()

        if b_data:

            sms_service.notify_customer(

                b_data['user_id'],

                compose_completed_sms(booking_id)

            )

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

            sms_service.notify_customer(

                d_data['user_id'],

                compose_driver_approved_sms(d_data['full_name'])

            )

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

            sms_service.notify_customer(

                d_data['user_id'],

                compose_driver_rejected_sms(reason)

            )

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

        # Notify all active admins about the new driver application
        try:
            sms_service.notify_admins(
                compose_admin_driver_application_sms(full_name)
            )
            notification_service.notify_admins_inapp(
                "New Driver Application",
                f"New driver application from {full_name}. Please review in the admin panel.",
                'admin_driver_application'
            )
        except Exception as sms_err:
            print(f"ERROR SENDING DRIVER APPLICATION SMS: {sms_err}")

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





@app.route('/api/admin/download-report', methods=['POST'])
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
        rev_query = "SELECT SUM(b.total_price) as total_revenue, COUNT(b.id) as total_bookings FROM bookings b JOIN vehicles v ON b.vehicle_id = v.id WHERE b.status != 'Cancelled'"
        rev_params = []
        rev_query, rev_params = apply_filters(rev_query, rev_params, 'b', 'v', skip_status=False)
        cur.execute(rev_query, tuple(rev_params))
        basic_stats = cur.fetchone()
        
        # 2. Daily Revenue (Last 30 days)
        trend_query = """
            SELECT TO_CHAR(b.start_date, 'YYYY-MM-DD') as day, SUM(b.total_price) as amount, COUNT(b.id) as booking_count
            FROM bookings b
            JOIN vehicles v ON b.vehicle_id = v.id
            WHERE b.start_date >= CURRENT_DATE - INTERVAL '30 days' AND b.status != 'Cancelled'
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
            SELECT v.brand, v.model, v.plate_number, COUNT(b.id) as booking_count, COALESCE(SUM(b.total_price), 0) as revenue
            FROM vehicles v
            JOIN bookings b ON v.id = b.vehicle_id
            WHERE b.status != 'Cancelled' AND b.payment_status = 'Paid'
        """
        top_params = []
        top_query, top_params = apply_filters(top_query, top_params, 'b', 'v', skip_status=False)
        top_query += " GROUP BY v.id, v.brand, v.model, v.plate_number ORDER BY revenue DESC LIMIT 5"
        cur.execute(top_query, tuple(top_params))
        top_vehicles = [{"brand": r.get('brand'), "model": r.get('model'), "plate_number": r.get('plate_number'), "booking_count": int(r.get('booking_count') or 0), "revenue": float(r.get('revenue') or 0)} for r in cur.fetchall()]

        return jsonify({
            "totalRevenue": float(basic_stats['total_revenue'] or 0),
            "totalBookings": basic_stats['total_bookings'] or 0,
            "revenueTrend": revenue_trend,
            "fleetDistribution": fleet_dist,
            "topVehicles": top_vehicles
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

            as_attachment=True,

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



@app.route('/validate-coupon', methods=['POST'])

def validate_coupon():

    data = request.json or {}

    code = data.get('code', '').strip().upper()

    

    if not code:

        return jsonify({"valid": False, "message": "No code provided"}), 400

        

    try:

        cur = get_cursor()

        query = """

            SELECT discount_percent FROM coupons 

            WHERE code = %s AND is_active = TRUE AND expiry_date >= CURRENT_DATE

        """

        cur.execute(query, (code,))

        coupon = cur.fetchone()

        

        if coupon:

            return jsonify({

                "valid": True, 

                "discount_percent": coupon['discount_percent']

            }), 200

        else:

            return jsonify({"valid": False, "message": "Invalid or expired code"}), 200

            

    except Exception as e:

        return jsonify({"valid": False, "error": str(e)}), 500

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

    print(f"DEBUG: admin_login called with data={request.json}")

    data = request.json

    if not data:

        return jsonify({"error": "No data received"}), 400

    email = data.get('email')

    password = data.get('password')

    

    try:

        cur = get_cursor()

        # Only allow is_verified = 1 (Active)

        cur.execute("SELECT id, full_name, role, assigned_location FROM users WHERE email=%s AND password=%s AND role IN ('admin', 'super_admin')", (email, password))

        user = cur.fetchone()

        

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

        return jsonify({"error": str(e)}), 400

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



        if password:

            cur.execute("UPDATE users SET full_name=%s, email=%s, password=%s, role=%s, assigned_location=%s WHERE id=%s", (name, email, password, role, assigned_location, user_id))

        else:

            cur.execute("UPDATE users SET full_name=%s, email=%s, role=%s, assigned_location=%s WHERE id=%s", (name, email, role, assigned_location, user_id))

        

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



        cur.execute("""

            INSERT INTO users (full_name, email, password, role, assigned_location, is_email_verified, is_verified)

            VALUES (%s, %s, %s, %s, %s, True, 1)

            RETURNING id

        """, (name, email, password, role, assigned_location))

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
        # Ensure color column exists
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS color VARCHAR(50) DEFAULT NULL")
        color = data.get('color') or None
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
            "INSERT INTO vehicles (brand, model, plate_number, vehicle_type, transmission, fuel_type, seats, location, status, daily_rate, vehicle_image, color) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (data.get('brand'), data.get('model'), data.get('plate_number'), data.get('vehicle_type'),
             data.get('transmission'), data.get('fuel_type'), data.get('seats'), data.get('location'),
             data.get('status', 'Available'), data.get('daily_rate'), vehicle_image, color)
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
        color = data.get('color') or None
        # Handle image upload if file provided
        vehicle_image = data.get('vehicle_image', '')
        if 'gallery' in request.files:
            files = request.files.getlist('gallery')
            if files and files[0].filename:
                file = files[0]
                filename = 'vehicle_' + str(vehicle_id) + '_' + str(__import__('time').time()) + '_' + file.filename
                file_data = file.read()
                try:
                    supabase.storage.from_('uploads').upload(path=filename, file=file_data, file_options={"content-type": file.content_type})
                    vehicle_image = supabase.storage.from_('uploads').get_public_url(filename)
                    cur.execute("INSERT INTO vehicle_images (vehicle_id, image_path, order_index) VALUES (%s, %s, %s)", (vehicle_id, vehicle_image, 0))
                except Exception:
                    pass
        cur.execute(
            "UPDATE vehicles SET brand=%s, model=%s, plate_number=%s, vehicle_type=%s, transmission=%s, fuel_type=%s, seats=%s, location=%s, status=%s, daily_rate=%s, vehicle_image=%s, color=%s WHERE id=%s",
            (data.get('brand'), data.get('model'), data.get('plate_number'), data.get('vehicle_type'),
             data.get('transmission'), data.get('fuel_type'), data.get('seats'), data.get('location'),
             data.get('status'), data.get('daily_rate'), vehicle_image, color, vehicle_id)
        )
        commit_db()
        return jsonify({"message": "Vehicle updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()



@app.route('/vehicles/<int:vehicle_id>', methods=['DELETE'])

def delete_vehicle(vehicle_id):

    try:

        cur = get_cursor()

        cur.execute("DELETE FROM vehicle_images WHERE vehicle_id = %s", (vehicle_id,))

        cur.execute("DELETE FROM vehicles WHERE id = %s", (vehicle_id,))

        commit_db()

        return jsonify({"message": "Vehicle deleted"}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

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

                MIN(vehicle_image) as vehicle_image,

                MIN(daily_rate) as daily_rate,

                MIN(vehicle_type) as vehicle_type,

                MIN(seats) as seats,

                MIN(fuel_type) as fuel_type,

                MIN(transmission) as transmission,

                MIN(location) as location,

                COUNT(*) as total_units,

                SUM(CASE WHEN status NOT IN ('Maintenance','Repair','Service','Sold','Booked') THEN 1 ELSE 0 END) as available_units

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



        cur.execute("UPDATE users SET password=%s WHERE id=%s", (new_password, user_id))

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



@app.route('/admin/activity-logs', methods=['GET'])

def get_activity_logs():

    try:

        cur = get_cursor()

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

            'rental_terms'

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
            "SUM(CASE WHEN status NOT IN ('Maintenance','Repair','Service','Sold','Booked') THEN 1 ELSE 0 END) as available "
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
    """Get all individual units for a brand+model, optionally filtered by color. Shows all statuses."""
    brand = request.args.get('brand', '')
    model = request.args.get('model', '')
    color = request.args.get('color', '')
    user_id = request.args.get('user_id', '')
    if not brand or not model:
        return jsonify({'error': 'brand and model are required'}), 400
    try:
        cur = get_cursor()
        if color and color != 'all' and color != 'Not Specified':
            cur.execute(
                "SELECT * FROM vehicles WHERE brand = %s AND model = %s AND COALESCE(color, 'Not Specified') = %s ORDER BY status ASC, id ASC",
                (brand, model, color)
            )
        else:
            cur.execute(
                "SELECT * FROM vehicles WHERE brand = %s AND model = %s ORDER BY status ASC, id ASC",
                (brand, model)
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
                      is_verified, loyalty_points,
                      license_number, license_expiry, license_type,
                      COALESCE(sms_opt_out, FALSE) AS sms_opt_out
               FROM users WHERE id = %s""",
            (user_id,)
        )
        user = cur.fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        d = dict(user)
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
        print(f"Error fetching license details for booking {booking_id}:", e)
        return jsonify({'error': str(e)}), 500

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

@app.route('/user/license-details', methods=['GET'])
def get_license_details():
    """Get the full driver's license details for a user."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        cur = get_cursor()
        cur.execute(
            """SELECT * FROM license_details WHERE user_id = %s""",
            (user_id,)
        )
        row = cur.fetchone()
        if row:
            d = dict(row)
            # convert dates to string
            if d.get('date_of_birth'): d['date_of_birth'] = str(d['date_of_birth'])
            if d.get('expiry_date'): d['expiry_date'] = str(d['expiry_date'])
            if d.get('created_at'): d['created_at'] = str(d['created_at'])
            if d.get('updated_at'): d['updated_at'] = str(d['updated_at'])
            return jsonify(d), 200
        else:
            return jsonify({}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/user/license-details', methods=['POST'])
def save_license_details():
    """Save or update full driver's license details."""
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        cur = get_cursor()
        
        full_name = request.form.get('full_name', '')
        date_of_birth = request.form.get('date_of_birth', '')
        license_number = request.form.get('license_number', '')
        expiry_date = request.form.get('expiry_date', '')
        issuing_country_state = request.form.get('issuing_country_state', '')
        license_class = request.form.get('license_class', '')
        emergency_contact_name = request.form.get('emergency_contact_name', '')
        emergency_contact_phone = request.form.get('emergency_contact_phone', '')
        emergency_contact_relationship = request.form.get('emergency_contact_relationship', '')
        
        front_url = request.form.get('license_front_url', '')
        back_url = request.form.get('license_back_url', '')

        # handle file uploads if present
        def upload_img(file_key, prefix):
            if file_key in request.files and request.files[file_key].filename:
                file = request.files[file_key]
                filename = f"{prefix}_{user_id}_{int(datetime.now().timestamp())}.jpg"
                file_data = file.read()
                try:
                    supabase.storage.from_('uploads').upload(path=filename, file=file_data, file_options={"content-type": "image/jpeg", "upsert": "true"})
                except Exception:
                    supabase.storage.from_('uploads').update(path=filename, file=file_data, file_options={"content-type": "image/jpeg"})
                return supabase.storage.from_('uploads').get_public_url(filename)
            return None

        new_front = upload_img('license_front_file', 'license_front')
        if new_front: front_url = new_front
        
        new_back = upload_img('license_back_file', 'license_back')
        if new_back: back_url = new_back

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
            """, (full_name, date_of_birth, license_number, expiry_date, issuing_country_state, license_class, emergency_contact_name, emergency_contact_phone, emergency_contact_relationship, front_url, back_url, user_id))
        else:
            cur.execute("""
                INSERT INTO license_details (
                    user_id, full_name, date_of_birth, license_number, expiry_date,
                    issuing_country_state, license_class, emergency_contact_name,
                    emergency_contact_phone, emergency_contact_relationship,
                    license_front_url, license_back_url
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, full_name, date_of_birth, license_number, expiry_date, issuing_country_state, license_class, emergency_contact_name, emergency_contact_phone, emergency_contact_relationship, front_url, back_url))
            
        cur.execute("UPDATE users SET is_verified = 1 WHERE id = %s", (user_id,))
        commit_db()
        return jsonify({'message': 'License details saved successfully', 'is_verified': 1}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/admin/fcm-token', methods=['POST'])
def register_admin_fcm_token():
    """Register or update an admin's FCM device token for push notifications."""
    data = request.get_json() or {}
    admin_id = data.get('admin_id')
    fcm_token = data.get('fcm_token')
    if not admin_id or not fcm_token:
        return jsonify({'error': 'admin_id and fcm_token are required'}), 400
    try:
        cur = get_cursor()
        cur.execute("UPDATE admins SET fcm_token = %s WHERE id = %s", (fcm_token, admin_id))
        commit_db()
        return jsonify({'message': 'Admin FCM token registered'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/user/fcm-token', methods=['POST'])
def register_fcm_token():
    """Register or update a user's FCM device token for push notifications.
    Request body: { "user_id": int, "fcm_token": str }
    """
    data = request.get_json() or {}
    user_id = data.get('user_id')
    fcm_token = data.get('fcm_token')
    if not user_id or not fcm_token:
        return jsonify({'error': 'user_id and fcm_token are required'}), 400
    try:
        cur = get_cursor()
        cur.execute(
            "UPDATE users SET fcm_token = %s WHERE id = %s",
            (fcm_token, user_id)
        )
        commit_db()
        return jsonify({'message': 'FCM token registered'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/user/sms-preference', methods=['POST'])
def update_sms_preference():
    """Update a user's SMS opt-out preference.

    Request body: { "user_id": int, "sms_opt_out": bool }
    Returns 200 with { "user_id": int, "sms_opt_out": bool } on success.
    Returns 400 on missing/invalid params, 404 if user not found.
    """
    data = request.get_json() or {}
    user_id = data.get('user_id')
    sms_opt_out = data.get('sms_opt_out')

    # Validate required parameters
    if user_id is None or sms_opt_out is None:
        return jsonify({'error': 'user_id and sms_opt_out are required'}), 400
    if not isinstance(sms_opt_out, bool):
        return jsonify({'error': 'sms_opt_out must be a boolean'}), 400

    try:
        cur = get_cursor()
        # Check user exists
        cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cur.fetchone():
            return jsonify({'error': 'User not found'}), 404
        # Update preference
        cur.execute(
            "UPDATE users SET sms_opt_out = %s WHERE id = %s",
            (sms_opt_out, user_id)
        )
        commit_db()
        return jsonify({'user_id': user_id, 'sms_opt_out': sms_opt_out}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/admin/sms-logs', methods=['GET'])
def get_sms_logs():
    """Return paginated SMS delivery logs ordered by created_at DESC.

    Query params:
      page          (int, default 1)
      per_page      (int, default 50)
      recipient_type (str, optional: 'customer' | 'driver' | 'admin')

    Response 200:
      { "logs": [...], "page": int, "per_page": int, "total": int }
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        recipient_type = request.args.get('recipient_type')

        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 50

        offset = (page - 1) * per_page

        cur = get_cursor()

        if recipient_type:
            cur.execute(
                "SELECT COUNT(*) AS total FROM sms_logs WHERE recipient_type = %s",
                (recipient_type,)
            )
        else:
            cur.execute("SELECT COUNT(*) AS total FROM sms_logs")

        total = cur.fetchone()['total']

        if recipient_type:
            cur.execute(
                """
                SELECT id, recipient_phone, recipient_type, recipient_id,
                       message_body, status, semaphore_response_code,
                       error_message, created_at
                FROM sms_logs
                WHERE recipient_type = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (recipient_type, per_page, offset)
            )
        else:
            cur.execute(
                """
                SELECT id, recipient_phone, recipient_type, recipient_id,
                       message_body, status, semaphore_response_code,
                       error_message, created_at
                FROM sms_logs
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (per_page, offset)
            )

        rows = cur.fetchall()
        logs = []
        for row in rows:
            entry = dict(row)
            # Serialize datetime to ISO string for JSON
            if entry.get('created_at'):
                entry['created_at'] = entry['created_at'].isoformat()
            logs.append(entry)

        return jsonify({
            'logs': logs,
            'page': page,
            'per_page': per_page,
            'total': total
        }), 200
    except Exception as e:
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
    """Debug: send a test push notification to an admin by admin_id."""
    data = request.get_json() or {}
    admin_id = data.get('admin_id')
    if not admin_id:
        return jsonify({'error': 'admin_id required'}), 400
    try:
        cur = get_cursor()
        cur.execute("SELECT id, username, fcm_token FROM admins WHERE id = %s", (int(admin_id),))
        admin = cur.fetchone()
        if not admin:
            return jsonify({'error': 'Admin not found'}), 404
        if not admin.get('fcm_token'):
            return jsonify({'error': 'No FCM token registered for this admin', 'admin': dict(admin)}), 400
        from notifications import fcm_service
        ok = fcm_service.send_push(admin['fcm_token'], 'Test Notification', 'Push notifications are working!')
        return jsonify({'success': ok, 'admin_id': admin_id, 'token_prefix': admin['fcm_token'][:20] + '...'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


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
    data = request.get_json() or {}
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
        user_id = request.args.get('user_id') or (request.get_json() or {}).get('user_id')
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
    data = request.get_json() or {}
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
    data = request.get_json() or {}
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
    Query param: admin_id (int, required)
    """
    admin_id = request.args.get('admin_id')
    if not admin_id:
        return jsonify({'error': 'admin_id is required'}), 400
    try:
        admin_id = int(admin_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'admin_id must be an integer'}), 400
    try:
        cur = get_cursor()
        cur.execute(
            """
            SELECT id, title, message, type, is_read, created_at
            FROM notifications
            WHERE admin_id = %s
            ORDER BY created_at DESC
            """,
            (admin_id,)
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


@app.route('/admin/notifications/read-all', methods=['POST'])
def mark_all_admin_notifications_read():
    """Mark all notifications as read for an admin.
    Request body: { "admin_id": int }
    """
    data = request.get_json() or {}
    admin_id = data.get('admin_id')
    if admin_id is None:
        return jsonify({'error': 'admin_id is required'}), 400
    try:
        admin_id = int(admin_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'admin_id must be an integer'}), 400
    try:
        cur = get_cursor()
        cur.execute(
            "UPDATE notifications SET is_read = TRUE WHERE admin_id = %s AND is_read = FALSE",
            (admin_id,)
        )
        updated = cur.rowcount
        commit_db()
        return jsonify({'updated': updated}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()


@app.route('/admin/notifications/<int:notif_id>/read', methods=['POST'])
def mark_admin_notification_read(notif_id):
    """Mark a single admin notification as read.
    Request body: { "admin_id": int }
    """
    data = request.get_json() or {}
    admin_id = data.get('admin_id')
    if admin_id is None:
        return jsonify({'error': 'admin_id is required'}), 400
    try:
        admin_id = int(admin_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'admin_id must be an integer'}), 400
    try:
        cur = get_cursor()
        cur.execute(
            "SELECT id, admin_id, title, message, type, is_read, created_at FROM notifications WHERE id = %s",
            (notif_id,)
        )
        notif = cur.fetchone()
        if not notif:
            return jsonify({'error': 'Notification not found'}), 404
        if notif['admin_id'] != admin_id:
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
    data = request.get_json() or {}
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
    data          = request.get_json() or {}
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
