import smtplib
import requests
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_PORT, EMAIL_USER, EMAIL_PASS, SEMAPHORE_API_KEY, SEMAPHORE_SENDER_NAME
from database import get_cursor

def send_notification(user_id, subject, message):
    """Sends notification to user via Email and SMS."""
    try:
        cur = get_cursor()
        cur.execute("SELECT email, phone_number, full_name FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if not user:
            return False
            
        email = user['email']
        phone = user['phone_number']
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
