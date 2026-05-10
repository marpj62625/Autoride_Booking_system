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
# Driver application compose functions
# ---------------------------------------------------------------------------

def compose_driver_approved_sms(driver_name) -> str:
    """SMS sent to a driver applicant when their application is approved."""
    return (
        f"Congratulations, {driver_name}! Your driver application has been approved. "
        f"You can now start accepting bookings."
    )


def compose_driver_rejected_sms(reason) -> str:
    """SMS sent to a driver applicant when their application is rejected."""
    return (
        f"Your driver application was not approved. Reason: {reason}. "
        f"You may re-apply once the issues are resolved."
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


def compose_admin_driver_application_sms(applicant_name) -> str:
    """Admin alert SMS when a new driver application is submitted."""
    return (
        f"New driver application from {applicant_name}. "
        f"Please review in the admin panel."
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
                    "SELECT phone_number, sms_opt_out FROM users WHERE id = %s",
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

            phone_number = user['phone_number']
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


# Module-level singleton — route handlers can do:
#   from notifications import sms_service
sms_service = SMS_Service()
