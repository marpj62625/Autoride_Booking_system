from flask import Blueprint, request, jsonify
from database import get_cursor, commit_db
import json
from notifications import (
    notification_service,
)

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/payment', methods=['POST'])
def process_payment():
    """Process a payment and update the corresponding booking status."""
    try:
        # Support both JSON and FormData (as checkout.html uses FormData for /payment)
        if request.is_json:
            data = request.json
        else:
            data = request.form

        booking_id = data.get('booking_id')
        amount = data.get('amount')
        method = data.get('method', 'Credit Card')
        reference_number = data.get('reference_number')

        if not booking_id:
            return jsonify({"error": "booking_id is required"}), 400

        cur = get_cursor()

        # 1. Insert into payments table
        cur.execute("""
            INSERT INTO payments (booking_id, amount, method, reference_number, status)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (booking_id, amount, method, reference_number, 'Completed'))
        
        payment_id = cur.fetchone()['id']

        # 2. Get booking details for points processing
        cur.execute("SELECT user_id, applied_coupon_id, points_redeemed, points_earned FROM bookings WHERE id = %s", (booking_id,))
        booking = cur.fetchone()

        if booking:
            user_id = booking['user_id']
            redeemed = booking['points_redeemed'] or 0
            earned = booking['points_earned'] or 0
            coupon_id = booking['applied_coupon_id']

            # Update User Loyalty Points (Redeem + Earn)
            # Logic: New Points = Current + Earned - Redeemed
            cur.execute("""
                UPDATE users 
                SET loyalty_points = loyalty_points + %s - %s 
                WHERE id = %s
            """, (earned, redeemed, user_id))

            # Update Coupon usage count if applicable
            if coupon_id:
                cur.execute("UPDATE coupons SET times_used = times_used + 1 WHERE id = %s", (coupon_id,))

        # 3. Update booking status to 'Confirmed' and payment_status to 'Paid' or 'Partially Paid'
        cur.execute("SELECT payment_type FROM bookings WHERE id = %s", (booking_id,))
        booking_info = cur.fetchone()
        new_payment_status = 'Paid'
        if booking_info and booking_info['payment_type'] == 'Downpayment':
            new_payment_status = 'Partially Paid'

        # Check if payment method is cash OTC
        is_cash = 'cash' in (method or '').lower() or 'over the counter' in (method or '').lower()
        
        if is_cash:
            # Cash OTC: Keep booking Pending, payment awaiting admin collection
            cur.execute("""
                UPDATE bookings 
                SET status = 'Pending', payment_status = 'Pending Payment'
                WHERE id = %s
            """, (booking_id,))
        else:
            # Online payment: auto-confirm
            cur.execute("""
                UPDATE bookings 
                SET status = 'Confirmed', payment_status = %s
                WHERE id = %s
            """, (new_payment_status, booking_id,))

        # 4. Update vehicle status to 'Booked'
        cur.execute("""
            UPDATE vehicles 
            SET status = 'Booked' 
            WHERE id = (SELECT vehicle_id FROM bookings WHERE id = %s)
        """, (booking_id,))

        commit_db()

        # 5. Send notification to customer
        try:
            cur.execute("""
                SELECT b.user_id, b.payment_type, b.balance_amount,
                       p.amount, p.method, p.reference_number
                FROM bookings b
                JOIN payments p ON p.booking_id = b.id
                WHERE b.id = %s AND p.id = %s
            """, (booking_id, payment_id))
            sms_data = cur.fetchone()
            if sms_data:
                user_id = sms_data['user_id']
                payment_type = sms_data['payment_type']
                amount = float(sms_data['amount'])
                method = sms_data['method']
                reference_number = sms_data['reference_number']
                balance_amount = float(sms_data['balance_amount'] or 0)
                if payment_type == 'Full':
                    notification_service.notify_user(
                        user_id,
                        "Payment Confirmed",
                        f"Payment confirmed for booking #{booking_id}. Amount: PHP {amount} via {method}. Ref: {reference_number}.",
                        'payment_confirmed'
                    )
                else:
                    notification_service.notify_user(
                        user_id,
                        "Downpayment Received",
                        f"Downpayment of PHP {amount} received for booking #{booking_id}. Ref: {reference_number}. Remaining balance: PHP {balance_amount}.",
                        'payment_downpayment'
                    )
                # Notify admins of new payment
                notification_service.notify_admins_inapp(
                    "New Payment Received",
                    f"Booking #{booking_id} - PHP {amount} via {method}. Ref: {reference_number}.",
                    'admin_payment_proof'
                )
        except Exception as notif_err:
            print(f"ERROR SENDING PAYMENT NOTIFICATION: {notif_err}")

        # 6. Send Email Receipt
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
            receipt_data = cur.fetchone()
            if receipt_data:
                from app import send_receipt_email
                print(f"DEBUG: Sending receipt email to {receipt_data['email']} for booking #{booking_id}")
                send_receipt_email(receipt_data['email'], dict(receipt_data))
                print(f"DEBUG: Receipt email sent successfully to {receipt_data['email']}")
            else:
                print(f"DEBUG: No receipt data found for booking #{booking_id}, payment #{payment_id}")
        except Exception as email_err:
            print(f"ERROR SENDING RECEIPT EMAIL for booking #{booking_id}: {email_err}")

        print(f"DEBUG: Payment received for booking {booking_id}. Payment ID: {payment_id}")
        return jsonify({
            "message": "Payment successful",
            "payment_id": payment_id,
            "status": "Confirmed"
        }), 200

    except Exception as e:
        print(f"PAYMENT ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500

@payment_bp.route('/bookings/<int:booking_id>/pay-balance', methods=['POST'])
def pay_balance(booking_id):
    """Process remaining balance payment via customer app."""
    try:
        data = request.json if request.is_json else request.form
        amount = data.get('amount')
        method = data.get('method', 'Credit Card')
        reference_number = data.get('reference_number')

        cur = get_cursor()
        
        # Verify booking status and balance
        cur.execute("SELECT id, payment_status, balance_amount, amount_paid FROM bookings WHERE id = %s", (booking_id,))
        booking = cur.fetchone()
        
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
            
        if booking['payment_status'] != 'Partially Paid' or float(booking['balance_amount'] or 0) <= 0:
            return jsonify({"error": "No balance to pay or booking already fully paid."}), 400

        # Insert into payments table
        cur.execute("""
            INSERT INTO payments (booking_id, amount, method, reference_number, status)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (booking_id, amount, method, reference_number, 'Completed'))
        payment_id = cur.fetchone()['id']

        # Update booking amounts and status
        new_amount_paid = float(booking['amount_paid'] or 0) + float(amount)
        cur.execute("""
            UPDATE bookings 
            SET amount_paid = %s, balance_amount = 0, payment_status = 'Paid'
            WHERE id = %s
        """, (new_amount_paid, booking_id))
        
        commit_db()
        print(f"DEBUG: Balance Payment received for booking {booking_id}. Payment ID: {payment_id}")

        # Send notification to customer
        try:
            cur.execute(
                "SELECT user_id FROM bookings WHERE id = %s",
                (booking_id,)
            )
            bk_row = cur.fetchone()
            if bk_row:
                notification_service.notify_user(
                    bk_row['user_id'],
                    "Balance Payment Received",
                    f"Balance payment of PHP {float(amount)} received for booking #{booking_id}. Ref: {reference_number}. Your booking is now fully paid.",
                    'payment_balance'
                )
        except Exception as notif_err:
            print(f"ERROR SENDING BALANCE PAYMENT NOTIFICATION: {notif_err}")

        return jsonify({
            "message": "Balance paid successfully",
            "payment_id": payment_id,
            "status": "Paid"
        }), 200

    except Exception as e:
        print(f"BALANCE PAYMENT ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500
