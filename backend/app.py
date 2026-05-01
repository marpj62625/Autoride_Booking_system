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
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Initialize database session management
init_db_helpers(app)

# Initialize Supabase Client for Storage
supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)

# Register Blueprints for modular routes
from routers.booking_routes import booking_bp
from routers.payment_routes import payment_bp
from routers.report_routes import report_bp
from utils.pdf_generator import generate_booking_pdf
import io
from flask import send_file

app.register_blueprint(booking_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(report_bp)

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

@app.route('/driver_portal/<path:filename>')
def serve_driver_portal(filename):
    return send_from_directory('../driver_portal', filename)

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

from notifications import send_notification

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
    """Sends a detailed booking receipt via SMTP."""
    subject = f"Autoride Receipt: Booking #{details['id']}"
    
    body = f"""
Hello {details['full_name']},

Thank you for choosing Autoride! Your payment has been received and your booking is confirmed.

--- RECEIPT DETAILS ---
Booking ID: #{details['id']}
Vehicle: {details['brand']} {details['model']}
Rental Period: {details['start_date']} to {details['end_date']}
Total Paid: PHP{float(details['total_price']):,.2f}
Reference Number: {details['reference_number']}
Payment Method: {details['method']}
Status: Confirmed

You can view your booking details and track your vehicle in your dashboard.
Safe travels!

The Autoride Team
    """
    
    # LOG TO TERMINAL
    print("\n" + "="*50)
    print(f"RECEIPT EMAIL LOG")
    print(f"TO: {email}")
    print(body)
    print("="*50 + "\n")

    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print(f"DEBUG: Receipt email sent to {email}")
    except Exception as e:
        print(f"DEBUG: Receipt SMTP Failed. Error: {str(e)}")

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

@app.route('/api/admin/verify-action', methods=['POST'])
def admin_verify_user():
    data = request.json
    user_id = data.get('user_id')
    status = data.get('status') # 2 for Verified, 0 for Rejected
    admin_id = data.get('admin_id')
    
    if not user_id or status is None:
        return jsonify({"error": "Missing parameters"}), 400
        
    try:
        cur = get_cursor()
        cur.execute("UPDATE users SET is_verified = %s WHERE id = %s", (status, user_id))
        
        # Log activity if admin_id is provided
        if admin_id:
            cur.execute("SELECT username FROM admins WHERE id = %s", (admin_id,))
            admin = cur.fetchone()
            admin_name = admin['username'] if admin else f"Admin {admin_id}"
            action_text = "Approved User Verification" if status == 2 else "Rejected User Verification"
            log_activity(admin_id, admin_name, action_text, "user", user_id)
            
        commit_db()
        return jsonify({"message": f"User status updated to {status}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/api/user/verify-status', methods=['GET'])
def check_verify_status():
    user_id = request.args.get('user_id')
    if not user_id: return jsonify({"error": "Missing user_id"}), 400
    try:
        cur = get_cursor()
        cur.execute("SELECT is_verified, license_image_url FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if not user: return jsonify({"error": "User not found"}), 404
        return jsonify(user), 200
    except Exception as e: return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/api/user/upload-license', methods=['POST'])
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
        filename = secure_filename(f"license_{user_id}_{int(datetime.now().timestamp())}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        url = f"/uploads/{filename}"
        
        # is_verified = 1 means 'Pending Review'
        cur.execute("UPDATE users SET license_image_url = %s, is_verified = 1 WHERE id = %s", (url, user_id))
        commit_db()
        return jsonify({"message": "License uploaded for verification", "url": url}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/api/admin/users', methods=['GET'])
@app.route('/api/admin/pending-verifications', methods=['GET'])
def admin_list_users():
    status = request.args.get('status')
    if request.path == '/api/admin/pending-verifications':
        status = 'pending'
        
    print(f"DEBUG: admin_list_users called with status={status} via path={request.path}")
    try:
        cur = get_cursor()
        if status == 'pending':
            # is_verified = 1 is Pending
            cur.execute("SELECT id, full_name, email, license_image_url as license_image, is_verified FROM users WHERE is_verified = 1 ORDER BY id DESC")
        else:
            cur.execute("SELECT id, full_name, email, license_image_url as license_image, is_verified FROM users ORDER BY id DESC")
        
        users = cur.fetchall()
        print(f"DEBUG: Found {len(users)} users matching criteria")
        return jsonify([dict(u) for u in users]), 200
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/api/user/points', methods=['GET'])
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
    credential = data.get('credential')
    is_driver = 1 if data.get('is_driver') else 0
    
    if not credential:
        return jsonify({"error": "No credential provided"}), 400

    try:
        # Verify the ID token using Google's libraries
        idinfo = id_token.verify_oauth2_token(credential, google_requests.Request(), GOOGLE_CLIENT_ID)

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
                    "user_id": user_fresh['id'], 
                    "full_name": user_fresh['full_name'],
                    "is_driver": user_fresh.get('is_driver', 0),
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
                    "user_id": new_user_id, 
                    "full_name": name,
                    "is_driver": is_driver,
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
        if not cur.fetchone():
            return jsonify({"error": "No account found with this phone number. Please register normally first."}), 404
            
        import random
        otp = str(random.randint(100000, 999999))
        temp_otps[phone] = otp
        
        # REAL SMS SENDING via Semaphore
        try:
            # Ensure number is in 11-digit local format for Semaphore (09XXXXXXXXX)
            formatted_phone = phone
            if phone.startswith('+63'):
                formatted_phone = '0' + phone[3:]
            elif not phone.startswith('0'):
                formatted_phone = '0' + phone

            print(f"DEBUG: Attempting to send SMS to {formatted_phone} via Semaphore...")
            
            response = requests.post("https://api.semaphore.co/api/v4/messages", data={
                'apikey': SEMAPHORE_API_KEY,
                'number': formatted_phone,
                'message': f"Your Autoride login code is: {otp}",
                'sendername': SEMAPHORE_SENDER_NAME
            })
            
            if response.status_code == 200:
                print(f"DEBUG: Semaphore SMS sent successfully!")
                return jsonify({"message": "OTP sent successfully to your mobile phone"}), 200
            else:
                raise Exception(f"Semaphore API Error: {response.text}")

        except Exception as sms_err:
            error_msg = str(sms_err)
            print(f"!!! SEMAPHORE SMS FAILED !!!")
            print(f"Error: {error_msg}")
            # FALLBACK FOR TESTING
            print(f"--------------------------------------------------")
            print(f"FALLBACK OTP for {phone}: {otp}")
            print(f"--------------------------------------------------")
            
            return jsonify({
                "error": "Failed to send SMS.",
                "message": f"Semaphore Error: {error_msg}. Check terminal for fallback code.",
                "debug_otp": otp
            }), 500
            
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


@app.route('/api/coupons/verify', methods=['POST'])
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

@app.route('/api/admin/upload-refund-proof', methods=['POST'])
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

@app.route('/api/vehicles/categories', methods=['GET'])
def get_vehicle_categories():
    user_id = request.args.get('user_id')
    favorites_only = request.args.get('favorites_only') == 'true'
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        cur = get_cursor()
        params = []

        # Category-Based Listing Logic
        # We group by major characteristics. We exclude transmission and specific daily_rate 
        # to ensure the same brand/model stay together.
        group_fields = "v.brand, v.model, v.vehicle_type, v.fuel_type, v.seats, v.location"
        
        # Base selection
        if user_id and user_id != 'null':
            select_clause = f"""
                SELECT {group_fields}, 
                MIN(v.id) as id,
                MAX(v.vehicle_image) as vehicle_image,
                MIN(v.daily_rate) as daily_rate,
                STRING_AGG(DISTINCT v.transmission, '/') as transmission,
                COUNT(*) as total_units,
                EXISTS(
                    SELECT 1 FROM favorites f 
                    JOIN vehicles v2 ON f.vehicle_id = v2.id 
                    WHERE v2.brand = v.brand AND v2.model = v.model AND f.user_id = %s
                ) as is_favorite
            """
            params.append(user_id)
        else:
            select_clause = f"""
                SELECT {group_fields}, 
                MIN(v.id) as id,
                MAX(v.vehicle_image) as vehicle_image,
                MIN(v.daily_rate) as daily_rate,
                STRING_AGG(DISTINCT v.transmission, '/') as transmission,
                COUNT(*) as total_units,
                FALSE as is_favorite
            """

        # Availability subquery for counting available units in the group
        if start_date and end_date:
            select_clause += f""",
                SUM(CASE WHEN NOT EXISTS (
                    SELECT 1 FROM bookings b 
                    WHERE b.vehicle_id = v.id 
                    AND b.status IN ('Confirmed', 'Pending', 'Picked Up')
                    AND (%s <= b.end_date AND %s >= b.start_date)
                ) THEN 1 ELSE 0 END) as available_units
            """
            params.extend([start_date, end_date])
        else:
            select_clause += ", SUM(CASE WHEN v.status = 'Available' THEN 1 ELSE 0 END) as available_units"

        # Determine location filter
        admin_id = request.args.get('admin_id')
        location_filter = None
        if admin_id and admin_id != 'null':
            cur.execute("SELECT role, assigned_location FROM users WHERE id = %s", (admin_id,))
            adm = cur.fetchone()
            if adm and adm['role'] == 'admin' and adm['assigned_location']:
                location_filter = adm['assigned_location']

        query = f"{select_clause} FROM vehicles v WHERE v.status NOT IN ('Maintenance', 'Repair', 'Service', 'Sold')"
        
        if location_filter:
            query += " AND v.location = %s "
            params.append(location_filter)
        
        if favorites_only and user_id and user_id != 'null':
            query += """ AND EXISTS (
                SELECT 1 FROM favorites f2 
                JOIN vehicles v3 ON f2.vehicle_id = v3.id 
                WHERE v3.brand = v.brand AND v3.model = v.model AND f2.user_id = %s
            )"""
            params.append(user_id)

        query += f" GROUP BY {group_fields}"
        
        cur.execute(query, params)
        vehicles = cur.fetchall()
        result = []
        for v in vehicles:
            v_dict = dict(v)
            try:
                cur.execute("SELECT id, image_path, is_primary, order_index FROM vehicle_images WHERE vehicle_id = %s ORDER BY order_index ASC, id ASC", (v_dict['id'],))
                gallery = cur.fetchall()
            except Exception:
                cur.execute("SELECT id, image_path, is_primary, id as order_index FROM vehicle_images WHERE vehicle_id = %s ORDER BY id ASC", (v_dict['id'],))
                gallery = cur.fetchall()

            v_dict['gallery_details'] = [dict(img) for img in gallery]
            v_dict['gallery'] = [img['image_path'] for img in gallery]
            v_dict['available_units'] = int(v_dict.get('available_units', 0))
            result.append(v_dict)
            
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()

@app.route('/vehicles', methods=['GET'])
def get_vehicles():
    user_id = request.args.get('user_id')
    favorites_only = request.args.get('favorites_only') == 'true'
    admin_id = request.args.get('admin_id')
    
    try:
        cur = get_cursor()
        
        # Determine location filter
        location_filter = None
        if admin_id and admin_id != 'null':
            cur.execute("SELECT role, assigned_location FROM users WHERE id = %s", (admin_id,))
            adm = cur.fetchone()
            if adm and adm['role'] == 'admin' and adm['assigned_location']:
                location_filter = adm['assigned_location']

        if user_id and user_id != 'null':
            query = """
                SELECT v.*, 
                EXISTS(SELECT 1 FROM favorites WHERE user_id = %s AND vehicle_id = v.id) as is_favorite
                FROM vehicles v
            """
            params = [user_id]
        else:
            query = "SELECT v.*, FALSE as is_favorite FROM vehicles v"
            params = []

        where_clauses = []
        if favorites_only and user_id and user_id != 'null':
            where_clauses.append("EXISTS(SELECT 1 FROM favorites WHERE user_id = %s AND vehicle_id = v.id)")
            params.append(user_id)
            
        if location_filter:
            where_clauses.append("v.location = %s")
            params.append(location_filter)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY v.id DESC"
        
        cur.execute(query, params)
        vehicles = cur.fetchall()
        result = []
        for v in vehicles:
            v_dict = dict(v)
            try:
                cur.execute("SELECT id, image_path, is_primary, order_index FROM vehicle_images WHERE vehicle_id = %s ORDER BY order_index ASC, id ASC", (v_dict['id'],))
                gallery = cur.fetchall()
            except Exception:
                cur.execute("SELECT id, image_path, is_primary, id as order_index FROM vehicle_images WHERE vehicle_id = %s ORDER BY id ASC", (v_dict['id'],))
                gallery = cur.fetchall()
            
            v_dict['gallery_details'] = [dict(img) for img in gallery]
            v_dict['gallery'] = [img['image_path'] for img in gallery]
            result.append(v_dict)
            
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()


@app.route('/vehicles', methods=['POST'])
def create_vehicle():
    try:
        # We now expect multipart/form-data
        name = request.form.get('name', '').strip()
        brand = request.form.get('brand', '').strip()
        model = request.form.get('model', '').strip()
        plate_number = request.form.get('plate_number', '').strip()
        vehicle_type = request.form.get('vehicle_type', '').strip()
        transmission = request.form.get('transmission', '').strip()
        fuel_type = request.form.get('fuel_type', '').strip()
        seats = request.form.get('seats')
        daily_rate = request.form.get('daily_rate')
        location = request.form.get('location', '').strip()
        status = request.form.get('status', 'Available').strip()
        
        # Backward compatibility for single image URL if provided
        vehicle_image = request.form.get('vehicle_image', '').strip()

        if not name or not brand or not model:
            return jsonify({"error": "name, brand, and model are required"}), 400

        cur = get_cursor()
        cur.execute("""
            INSERT INTO vehicles (name, brand, model, plate_number, vehicle_type, transmission, fuel_type, seats, daily_rate, location, status, vehicle_image)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (name, brand, model, plate_number, vehicle_type, transmission, fuel_type, seats, daily_rate, location, status, vehicle_image))
        vehicle_id = cur.fetchone()['id']
        
        # Handle Gallery Uploads
        if 'gallery' in request.files:
            files = request.files.getlist('gallery')
            image_urls = []
            for i, file in enumerate(files):
                if file.filename != '':
                    filename = secure_filename(f"vehicle_{vehicle_id}_{i}_{file.filename}")
                    file_content = file.read()
                    bucket_name = "uploads"
                    path_on_supa = f"vehicles/{filename}"
                    
                    try:
                        supabase.storage.from_(bucket_name).upload(
                            path=path_on_supa,
                            file=file_content,
                            file_options={"content-type": file.content_type, "upsert": "true"}
                        )
                        public_url = supabase.storage.from_(bucket_name).get_public_url(path_on_supa)
                        image_urls.append(public_url)
                        
                        # Save to vehicle_images table
                        cur.execute("""
                            INSERT INTO vehicle_images (vehicle_id, image_path, is_primary)
                            VALUES (%s, %s, %s)
                        """, (vehicle_id, public_url, True if i == 0 and not vehicle_image else False))
                        
                        # Update primary image if this is the first one and no URL was provided
                        if i == 0 and not vehicle_image:
                            cur.execute("UPDATE vehicles SET vehicle_image = %s WHERE id = %s", (public_url, vehicle_id))
                            
                    except Exception as storage_err:
                        print(f"STORAGE ERROR: {str(storage_err)}")

        commit_db()
        return jsonify({"message": "Vehicle created", "vehicle_id": vehicle_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()

@app.route('/vehicles/<int:vehicle_id>', methods=['PUT'])
def update_vehicle(vehicle_id):
    try:
        # Support both JSON (old) and Form Data (new)
        if request.is_json:
            data = request.json
        else:
            data = request.form

        name = data.get('name', '').strip()
        brand = data.get('brand', '').strip()
        model = data.get('model', '').strip()
        plate_number = data.get('plate_number', '').strip()
        vehicle_type = data.get('vehicle_type', '').strip()
        transmission = data.get('transmission', '').strip()
        fuel_type = data.get('fuel_type', '').strip()
        seats = data.get('seats')
        daily_rate = data.get('daily_rate')
        location = data.get('location', '').strip()
        status = data.get('status', '').strip()
        vehicle_image = data.get('vehicle_image', '').strip()

        if not name or not brand or not model:
            return jsonify({"error": "name, brand, and model are required"}), 400

        cur = get_cursor()
        cur.execute("SELECT id FROM vehicles WHERE id = %s", (vehicle_id,))
        if not cur.fetchone():
            return jsonify({"error": "Vehicle not found"}), 404

        cur.execute("""
            UPDATE vehicles
            SET name = %s, brand = %s, model = %s, plate_number = %s, vehicle_type = %s, transmission = %s, fuel_type = %s, seats = %s, daily_rate = %s, location = %s, status = %s, vehicle_image = %s
            WHERE id = %s
        """, (name, brand, model, plate_number, vehicle_type, transmission, fuel_type, seats, daily_rate, location, status, vehicle_image, vehicle_id))

        # Handle Gallery Uploads (Append or Refresh?)
        # Let's say if new images are provided, we add them. 
        # If user wants to clear, we might need another endpoint, but for now let's just append.
        if 'gallery' in request.files:
            files = request.files.getlist('gallery')
            for i, file in enumerate(files):
                if file.filename != '':
                    import time
                    timestamp = int(time.time())
                    filename = secure_filename(f"vehicle_{vehicle_id}_{timestamp}_{i}_{file.filename}")
                    file_content = file.read()
                    bucket_name = "uploads"
                    path_on_supa = f"vehicles/{filename}"
                    
                    try:
                        supabase.storage.from_(bucket_name).upload(
                            path=path_on_supa,
                            file=file_content,
                            file_options={"content-type": file.content_type, "upsert": "true"}
                        )
                        public_url = supabase.storage.from_(bucket_name).get_public_url(path_on_supa)
                        
                        try:
                            cur.execute("""
                                INSERT INTO vehicle_images (vehicle_id, image_path, is_primary, order_index)
                                VALUES (%s, %s, %s, %s)
                            """, (vehicle_id, public_url, False, i + 100))
                        except Exception:
                            # Fallback if order_index doesn't exist
                            cur.execute("""
                                INSERT INTO vehicle_images (vehicle_id, image_path, is_primary)
                                VALUES (%s, %s, %s)
                            """, (vehicle_id, public_url, False))
                        
                        # If vehicle has no primary image, set this one
                        if not vehicle_image:
                            cur.execute("UPDATE vehicles SET vehicle_image = %s WHERE id = %s", (public_url, vehicle_id))
                            vehicle_image = public_url

                    except Exception as storage_err:
                        print(f"STORAGE ERROR: {str(storage_err)}")

        commit_db()
        return jsonify({"message": "Vehicle updated", "vehicle_id": vehicle_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()

@app.route('/vehicles/<int:vehicle_id>', methods=['DELETE'])
def delete_vehicle(vehicle_id):
    try:
        cur = get_cursor()
        cur.execute("SELECT id FROM vehicles WHERE id = %s", (vehicle_id,))
        if not cur.fetchone():
            return jsonify({"error": "Vehicle not found"}), 404

        # Delete from favorites, reviews, and vehicle_images
        cur.execute("DELETE FROM favorites WHERE vehicle_id = %s", (vehicle_id,))
        cur.execute("DELETE FROM reviews WHERE vehicle_id = %s", (vehicle_id,))
        cur.execute("DELETE FROM vehicle_images WHERE vehicle_id = %s", (vehicle_id,))
        
        # Cascade delete bookings and their payments
        cur.execute("SELECT id FROM bookings WHERE vehicle_id = %s", (vehicle_id,))
        bookings = cur.fetchall()
        for b in bookings:
            cur.execute("DELETE FROM payments WHERE booking_id = %s", (b['id'],))
            cur.execute("DELETE FROM split_payments WHERE booking_id = %s", (b['id'],))
            
        cur.execute("DELETE FROM bookings WHERE vehicle_id = %s", (vehicle_id,))

        # Finally delete the vehicle
        cur.execute("DELETE FROM vehicles WHERE id = %s", (vehicle_id,))
        commit_db()
        return jsonify({"message": "Vehicle deleted", "vehicle_id": vehicle_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()

# --- GPS TRACKING ROUTES ---
@app.route('/api/vehicles/<int:vehicle_id>/location', methods=['POST'])
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

@app.route('/api/admin/gps-locations', methods=['GET'])
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

@app.route('/api/vehicles/images/<int:image_id>', methods=['DELETE'])
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

        # Log activity if admin info is available
        # Note: We should ideally pass admin_id/name from frontend, 
        # but for now let's log as system if not provided
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

@app.route('/api/vehicles/<int:vehicle_id>/images/order', methods=['PUT'])
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

@app.route('/api/maintenance/migrate', methods=['GET'])
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

        # New fields
        addons = ",".join(data.get('addons', []))
        base_price = data.get('base_price')
        addon_price = data.get('addon_price')
        tax_amount = data.get('tax_amount')
        total_price = data.get('total_price')

        cur.execute("""
            INSERT INTO bookings (
                user_id, vehicle_id, start_date, end_date, pickup_location, rental_type, addons, 
                base_price, addon_price, tax_amount, total_price, status,
                pickup_province, pickup_municipality, pickup_barangay,
                return_province, return_municipality, return_barangay
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending', %s, %s, %s, %s, %s, %s) RETURNING id
        """, (user_id, final_vehicle_id, start_date, end_date, pickup_location, rental_type, addons, 
              base_price, addon_price, tax_amount, total_price,
              pickup_province, pickup_municipality, pickup_barangay,
              return_province, return_municipality, return_barangay))
        
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

@app.route('/payment', methods=['POST'])
def payment():
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
            SELECT b.id, u.email, u.full_name, v.brand, v.model, b.start_date, b.end_date, b.total_price, 
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
        # Fetch bookings with vehicle info
        query = """
            SELECT b.*, v.brand, v.model, v.plate_number 
            FROM bookings b
            JOIN vehicles v ON b.vehicle_id = v.id
            WHERE b.user_id = %s
            ORDER BY b.start_date DESC
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
        cur.execute("SELECT status FROM bookings WHERE id=%s", (booking_id,))
        bk = cur.fetchone()
        if bk and bk['status'] == 'Pending':
            cur.execute("UPDATE bookings SET status='Cancelled' WHERE id=%s", (booking_id,))
            
            # Reset vehicle status to 'Available'
            cur.execute("UPDATE vehicles SET status='Available' WHERE id=(SELECT vehicle_id FROM bookings WHERE id=%s)", (booking_id,))
            
            commit_db()
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
            
        cur.execute("""
            UPDATE bookings 
            SET start_date = %s, end_date = %s, total_price = %s 
            WHERE id = %s
        """, (new_start, new_end, new_total, booking_id))
        
        commit_db()
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
        
        # Send Notification
        cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))
        b_data = cur.fetchone()
        if b_data:
            send_notification(
                user_id=b_data['user_id'],
                subject="Booking Approved! - Autoride",
                message=f"Good news! Your booking #{booking_id} has been approved. You can now prepare for your trip."
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
        
        # Send Notification
        send_notification(
            user_id=booking['user_id'],
            subject="Booking Cancelled",
            message=f"Your booking #{booking_id} has been successfully cancelled."
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
        
        # Send Notification
        send_notification(
            user_id=row['user_id'],
            subject="Booking Rejected - Autoride",
            message=f"Unfortunately, your booking #{booking_id} has been rejected. Please contact support for more information."
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

        # Send Notification
        send_notification(
            user_id=booking['user_id'],
            subject="Booking Cancelled - Autoride",
            message=f"Your booking #{booking_id} has been cancelled. A refund has been initiated if applicable."
        )

        return jsonify({"message": f"Booking #{booking_id} cancelled. Payment status: {new_payment_status}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/api/inspections/submit', methods=['POST'])
def submit_inspection():
    """Submit a vehicle inspection with multiple photos."""
    try:
        booking_id = request.form.get('booking_id')
        inspection_type = request.form.get('type') # 'pickup' or 'return'
        mileage = request.form.get('mileage')
        fuel_level = request.form.get('fuel_level')
        notes = request.form.get('notes')
        inspector_id = request.form.get('admin_id') # Who is submitting

        if not booking_id or not inspection_type:
            return jsonify({"error": "Missing booking_id or inspection_type"}), 400

        # Handle multiple photo uploads
        uploaded_photos = []
        if 'photos' in request.files:
            files = request.files.getlist('photos')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(f"insp_{booking_id}_{inspection_type}_{datetime.now().timestamp()}_{file.filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    uploaded_photos.append(f"/uploads/{filename}")

        cur = get_cursor()
        cur.execute("""
            INSERT INTO vehicle_inspections (booking_id, inspection_type, photos, mileage, fuel_level, notes, inspector_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (booking_id, inspection_type, json.dumps(uploaded_photos), mileage, fuel_level, notes, inspector_id))
        inspection_id = cur.fetchone()['id']
        
        # Log the activity
        log_activity(
            admin_id=inspector_id,
            admin_name="Staff/Driver",
            action=f'SUBMIT_{inspection_type.upper()}_INSPECTION',
            target_type='VEHICLE',
            target_id=str(booking_id),
            details=f"Submitted {inspection_type} inspection for booking #{booking_id}. Photos: {len(uploaded_photos)}"
        )
        
        commit_db()
        return jsonify({"message": f"{inspection_type.capitalize()} inspection submitted", "id": inspection_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/api/inspections/<int:booking_id>', methods=['GET'])
def get_inspections(booking_id):
    """Retrieve all inspections for a specific booking."""
    try:
        cur = get_cursor()
        cur.execute("SELECT * FROM vehicle_inspections WHERE booking_id = %s ORDER BY created_at ASC", (booking_id,))
        inspections = cur.fetchall()
        return jsonify(inspections), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/bookings/<int:booking_id>/pickup', methods=['PUT'])
def pickup_booking(booking_id):
    """Mark a booking as Picked Up."""
    try:
        cur = get_cursor()
        cur.execute("UPDATE bookings SET status='Picked Up' WHERE id=%s", (booking_id,))
        commit_db()
        
        # Send Notification
        cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))
        b_data = cur.fetchone()
        if b_data:
            send_notification(
                user_id=b_data['user_id'],
                subject="Vehicle Picked Up - Autoride",
                message=f"Drive safely! You have officially picked up the vehicle for booking #{booking_id}."
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
        
        # Send Notification
        cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))
        b_data = cur.fetchone()
        if b_data:
            send_notification(
                user_id=b_data['user_id'],
                subject="Rental Completed - Autoride",
                message=f"Thank you for choosing Autoride! Your booking #{booking_id} is now completed. We hope to see you again soon."
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
        
        # Send Notification
        cur.execute("SELECT user_id FROM drivers WHERE id = %s", (driver_id,))
        d_data = cur.fetchone()
        if d_data:
            send_notification(
                user_id=d_data['user_id'],
                subject="Driver Application Approved! - Autoride",
                message="Congratulations! Your driver application has been approved. You can now start accepting bookings."
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
        
        # Send Notification
        cur.execute("SELECT user_id FROM drivers WHERE id = %s", (driver_id,))
        d_data = cur.fetchone()
        if d_data:
            send_notification(
                user_id=d_data['user_id'],
                subject="Driver Application Update - Autoride",
                message=f"Your driver application has been rejected. Reason: {reason}. You can re-apply once the issues are resolved."
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


@app.route('/api/admin/detailed-stats', methods=['GET'])
def get_detailed_stats():
    """Aggregated stats for the executive dashboard charts."""
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

        # 1. Revenue & Bookings
        rev_query = "SELECT SUM(b.total_price) as total_revenue, COUNT(b.id) as total_bookings FROM bookings b JOIN vehicles v ON b.vehicle_id = v.id WHERE b.status != 'Cancelled'"
        rev_params = []
        if location_filter:
            rev_query += " AND v.location = %s"
            rev_params.append(location_filter)
            
        cur.execute(rev_query, tuple(rev_params))
        basic_stats = cur.fetchone()
        
        # 2. Daily Revenue (Last 30 days)
        trend_query = """
            SELECT TO_CHAR(b.start_date, 'YYYY-MM-DD') as day, SUM(b.total_price) as amount
            FROM bookings b
            JOIN vehicles v ON b.vehicle_id = v.id
            WHERE b.start_date >= CURRENT_DATE - INTERVAL '30 days' AND b.status != 'Cancelled'
        """
        trend_params = []
        if location_filter:
            trend_query += " AND v.location = %s"
            trend_params.append(location_filter)
            
        trend_query += " GROUP BY day ORDER BY day ASC"
        cur.execute(trend_query, tuple(trend_params))
        revenue_trend = cur.fetchall()
        
        # 3. Fleet Distribution
        fleet_query = "SELECT status, COUNT(*) as count FROM vehicles"
        fleet_params = []
        if location_filter:
            fleet_query += " WHERE location = %s"
            fleet_params.append(location_filter)
        
        fleet_query += " GROUP BY status"
        cur.execute(fleet_query, tuple(fleet_params))
        fleet_dist = cur.fetchall()
        
        # 4. Top Performing Vehicles
        top_query = """
            SELECT v.brand, v.model, COUNT(b.id) as booking_count, SUM(b.total_price) as revenue
            FROM vehicles v
            JOIN bookings b ON v.id = b.vehicle_id
            WHERE b.status != 'Cancelled'
        """
        top_params = []
        if location_filter:
            top_query += " AND v.location = %s"
            top_params.append(location_filter)
            
        top_query += " GROUP BY v.id, v.brand, v.model ORDER BY revenue DESC LIMIT 5"
        cur.execute(top_query, tuple(top_params))
        top_vehicles = cur.fetchall()

        # 5. User Stats (Enhanced Breakdown)
        # Email Stats
        cur.execute("SELECT is_email_verified, COUNT(*) as count FROM users GROUP BY is_email_verified")
        email_rows = cur.fetchall()
        email_stats = {
            "verified": next((int(r['count']) for r in email_rows if r['is_email_verified'] is True), 0),
            "unverified": next((int(r['count']) for r in email_rows if r['is_email_verified'] is False), 0)
        }

        # License Status
        cur.execute("SELECT is_verified, COUNT(*) as count FROM users GROUP BY is_verified")
        id_rows = cur.fetchall()
        license_stats = {
            "pending": next((int(r['count']) for r in id_rows if r['is_verified'] == 0), 0),
            "approved": next((int(r['count']) for r in id_rows if r['is_verified'] == 1), 0),
            "rejected": next((int(r['count']) for r in id_rows if r['is_verified'] == 2), 0)
        }
        
        return jsonify({
            "summary": dict(basic_stats) if basic_stats else {"total_revenue": 0, "total_bookings": 0},
            "revenueTrend": [dict(r) for r in revenue_trend],
            "fleetDistribution": [dict(f) for f in fleet_dist],
            "topVehicles": [dict(v) for v in top_vehicles],
            "userStats": {
                "email": email_stats,
                "license": license_stats
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()

@app.route('/api/bookings/<int:booking_id>/receipt', methods=['GET'])
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


@app.route('/api/support', methods=['POST'])
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

@app.route('/api/admin/support', methods=['GET'])
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

@app.route('/api/admin/support/<int:ticket_id>', methods=['PUT'])
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

@app.route('/api/admin/instructions', methods=['GET', 'POST'])
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

@app.route('/api/newsletter', methods=['POST'])
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

@app.route('/api/validate-coupon', methods=['POST'])
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

@app.route('/api/admin/pending-verifications', methods=['GET'])
def get_pending_verifications():
    try:
        cur = get_cursor()
        # is_verified = 0 means uploaded but pending, 2 means rejected, 1 means verified
        cur.execute("SELECT id, full_name, email, license_image, is_verified FROM users WHERE license_image IS NOT NULL AND is_verified IN (0, 2)")
        users = cur.fetchall()
        return jsonify([dict(u) for u in users]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()

@app.route('/api/admin/verify-user', methods=['POST'])
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
        "response": "Hello! 👋 Welcome to Autoride! I'm your virtual assistant. I can help you with:\n\n• Booking a vehicle\n• Pricing & rates\n• Requirements & documents\n• Cancellation policy\n• Payment methods\n• Driver services\n\nWhat would you like to know?"
    },
    {
        "keywords": ["how to book", "booking", "rent", "reserve", "paano mag book", "pano mag rent", "how to rent"],
        "response": "📋 **How to Book a Vehicle:**\n\n1. Browse our vehicle catalog on the homepage\n2. Click on the vehicle you want\n3. Select your rental dates (start & end)\n4. Choose pickup & return locations\n5. Select add-ons (driver, insurance, etc.)\n6. Review the total and proceed to checkout\n7. Complete payment to confirm your booking!\n\nNeed help with a specific step?"
    },
    {
        "keywords": ["price", "rate", "cost", "how much", "magkano", "presyo", "fee", "pricing", "daily rate"],
        "response": "💰 **Pricing Information:**\n\nOur rates vary by vehicle type:\n• **Cars** — Starting at PHP1,500/day\n• **SUVs** — Starting at PHP2,500/day\n• **Vans** — Starting at PHP3,000/day\n• **Trucks** — Starting at PHP3,500/day\n\nRates include basic insurance. Add-ons like a professional driver (+PHP500/day) are available.\n\nYou can see exact pricing on each vehicle's detail page!"
    },
    {
        "keywords": ["requirement", "document", "need to bring", "valid id", "license", "ano kailangan", "requirements"],
        "response": "📄 **Requirements for Renting:**\n\n1. **Valid Government ID** (Driver's License, Passport, or National ID)\n2. **Proof of Address** (Utility bill or bank statement)\n3. **Valid Driver's License** (if self-drive)\n4. **Security Deposit** (varies per vehicle)\n5. Must be **21 years or older**\n\nFor corporate rentals, additional documents may be needed. Contact support for details!"
    },
    {
        "keywords": ["cancel", "cancellation", "refund", "change booking", "reschedule", "cancel booking", "pano mag cancel"],
        "response": "🔄 **Cancellation & Refund Policy:**\n\n• **Free cancellation** if done 48+ hours before pickup\n• **50% refund** if cancelled 24-48 hours before\n• **No refund** if cancelled less than 24 hours before\n• **Rescheduling** is free if done 24+ hours before\n\nTo cancel or reschedule, go to your Dashboard → My Bookings → select the booking → Cancel/Reschedule."
    },
    {
        "keywords": ["payment", "pay", "gcash", "maya", "credit card", "bayad", "paano magbayad", "payment method"],
        "response": "💳 **Payment Methods:**\n\nWe accept the following:\n• **Credit/Debit Cards** (Visa, Mastercard)\n• **GCash**\n• **Maya (PayMaya)**\n• **Bank Transfer**\n• **Cash** (at pickup location)\n\nPayment is required to confirm your booking. You'll receive a receipt via email."
    },
    {
        "keywords": ["driver", "chauffeur", "may driver", "with driver", "hire driver", "professional driver"],
        "response": "🚗 **Driver Services:**\n\nYes! We offer professional drivers as an add-on:\n\n• **Cost:** Additional PHP500/day\n• **Licensed & verified** professional drivers\n• **Available for all vehicle types**\n• Select the 'With Driver' option during booking\n\nOur drivers are thoroughly vetted, licensed, and experienced. Perfect for long trips or if you prefer not to drive!"
    },
    {
        "keywords": ["insurance", "coverage", "accident", "damage", "protection"],
        "response": "🛡️ **Insurance & Coverage:**\n\n• **Basic Insurance** — Included free with every rental\n• **Premium Insurance** — Available as add-on for comprehensive coverage\n• Covers collision damage, theft, and third-party liability\n• Deductible may apply for certain claims\n\nWe recommend premium insurance for peace of mind on longer trips!"
    },
    {
        "keywords": ["pickup", "location", "where", "saan", "branch", "drop off", "return", "delivery"],
        "response": "📍 **Pickup & Return Locations:**\n\nYou set your preferred pickup and return locations during booking:\n• Enter your **Province, Municipality, and Barangay**\n• Separate pickup and return locations are supported\n• Delivery to your location may be available\n\nExact availability depends on vehicles in your area."
    },
    {
        "keywords": ["register", "sign up", "create account", "gawa account", "account"],
        "response": "📝 **Creating an Account:**\n\n1. Click **Register** on the top right\n2. Enter your full name, email, and password\n3. Verify your email address\n4. Complete your profile with contact info\n5. You're ready to book!\n\nYou can also sign in with Google for faster access."
    },
    {
        "keywords": ["forgot password", "reset password", "can't login", "hindi makapasok", "password reset"],
        "response": "🔐 **Password Reset:**\n\nIf you forgot your password:\n1. Go to the Login page\n2. Click 'Forgot Password'\n3. Enter your registered email\n4. Check your inbox for the reset link\n5. Set a new password\n\nStill can't access your account? Submit a support ticket and we'll help!"
    },
    {
        "keywords": ["contact", "phone", "email", "support", "help", "customer service", "tulong"],
        "response": "📞 **Contact Us:**\n\n• **Support Page:** Visit our Support page to submit a ticket\n• **Response Time:** Within 24 hours\n• **Live Chat:** You're using it right now! 😊\n\nFor urgent concerns, submit a support ticket with subject 'URGENT' and we'll prioritize your request."
    },
    {
        "keywords": ["promo", "coupon", "discount", "code", "voucher", "sale"],
        "response": "🎉 **Promos & Discounts:**\n\nWe regularly offer promotional codes! Here's how to use one:\n1. Select your vehicle and set your dates\n2. In the booking form, find the **Promo Code** field\n3. Enter your code and click **Apply**\n4. The discount will be reflected in your total\n\nFollow us on social media for the latest promos!"
    },
    {
        "keywords": ["fuel", "gas", "gasoline", "diesel", "petrol", "fuel policy"],
        "response": "⛽ **Fuel Policy:**\n\n• Vehicles are provided with a **full tank**\n• Please return the vehicle with a **full tank**\n• If returned with less fuel, a refueling charge applies\n• Fuel type is listed on each vehicle's detail page (Petrol, Diesel, Hybrid, Electric)"
    },
    {
        "keywords": ["age", "minimum age", "how old", "edad", "age limit"],
        "response": "👤 **Age Requirements:**\n\n• Minimum age: **21 years old**\n• Must have a valid driver's license (for self-drive)\n• Drivers under 25 may be subject to a young driver surcharge\n• No maximum age limit (valid license required)"
    },
    {
        "keywords": ["thank", "thanks", "salamat", "ok", "okay", "got it", "sige"],
        "response": "You're welcome! 😊 Happy to help. If you have any more questions, just type away. Enjoy your ride with Autoride! 🚗✨"
    },
    {
        "keywords": ["apply driver", "become driver", "mag apply", "driver application"],
        "response": "🚘 **Apply as a Driver:**\n\n1. Click **Apply as Driver** on the homepage\n2. Fill in your full name, license number, and contact info\n3. Upload your driver's license document\n4. Submit your application\n5. Wait for admin approval (usually within 24-48 hours)\n\nOnce approved, you'll be able to accept driving assignments!"
    },
    {
        "keywords": ["status", "booking status", "where is", "track", "update"],
        "response": "📊 **Check Your Booking Status:**\n\n1. Log in to your account\n2. Go to **Dashboard** (click your profile or the Dashboard link)\n3. Find your booking under **My Bookings**\n4. Status will show: Pending, Confirmed, Active, or Completed\n\nYou'll also receive email notifications for status changes!"
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
    return ("I'm not sure I understand that question. 🤔\n\nHere are some things I can help with:\n"
            "• **Booking** — How to rent a vehicle\n"
            "• **Pricing** — Rates and costs\n"
            "• **Requirements** — Documents needed\n"
            "• **Cancellation** — Refund policy\n"
            "• **Payment** — Payment methods\n"
            "• **Driver** — Hire a professional driver\n\n"
            "Or you can visit our **Support** page to submit a ticket for personalized assistance!")


@app.route('/api/chat', methods=['POST'])
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



@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    try:
        cur = get_cursor()
        # Only allow is_verified = 1 (Active)
        cur.execute("SELECT id, full_name, role, assigned_location FROM users WHERE email=%s AND password=%s AND role IN ('admin', 'super_admin') AND is_verified = 1", (email, password))
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

@app.route('/api/admin/list', methods=['GET'])
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

@app.route('/api/admin/update/<int:user_id>', methods=['PUT'])
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

@app.route('/api/admin/delete/<int:user_id>', methods=['DELETE'])
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

@app.route('/api/admin/status/<int:user_id>', methods=['PUT'])
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

@app.route('/api/admin/create', methods=['POST'])
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


@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    admin_id = request.args.get('admin_id')
    
    try:
        cur = get_cursor()
        cur.execute("SELECT role, assigned_location FROM users WHERE id=%s", (admin_id,))
        admin = cur.fetchone()
        
        if not admin or admin['role'] not in ['admin', 'super_admin']:
            return jsonify({"error": "Forbidden"}), 403

        location_filter = admin['assigned_location'] if admin['role'] == 'admin' else None

        # Common stats
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

        # Revenue restricted to Super Admin or Branch Admin (for their own branch)
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

@app.route('/api/admin/change-password', methods=['POST'])
def change_admin_password():
    data = request.json
    user_id = data.get('user_id')
    new_password = data.get('new_password')

    if not user_id or not new_password:
        return jsonify({"error": "Missing user_id or password"}), 400

    try:
        cur = get_cursor()
        # Verify user exists and is an admin
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
        
@app.route('/api/admin/settings', methods=['GET', 'POST'])
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
            # Verify super_admin role
            cur.execute("SELECT full_name, role FROM users WHERE id=%s", (requester_id,))
            user = cur.fetchone()
            if not user or user['role'] != 'super_admin':
                return jsonify({"error": "Unauthorized. Super Admin only."}), 403

            for item in updates:
                cur.execute("UPDATE settings SET value=%s, updated_at=CURRENT_TIMESTAMP WHERE key=%s", (str(item['value']), item['key']))
            
            commit_db()

            # Log activity
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

@app.route('/api/admin/activity-logs', methods=['GET'])
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

@app.route('/api/public/settings', methods=['GET'])
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=True)
