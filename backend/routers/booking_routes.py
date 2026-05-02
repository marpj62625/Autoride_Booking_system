from flask import Blueprint, request, jsonify
from database import get_cursor, commit_db
import json
from notifications import send_notification

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/book', methods=['POST'])
def book_vehicle():
    """Create a new booking in the database."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing booking data"}), 400

        user_id = data.get('user_id')
        vehicle_id = data.get('vehicle_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        pickup_location = data.get('pickup_location')
        rental_type = data.get('rental_type', 'Self-Drive')
        
        # Prices
        base_price = data.get('base_price', 0)
        addon_price = data.get('addon_price', 0)
        total_price = data.get('total_price', 0)

        # Optional fields
        driver_id = data.get('driver_id')
        addons = json.dumps(data.get('addons', []))
        insurance_type = data.get('insurance_type', 'Basic')
        insurance_price = data.get('insurance_price', 0)
        
        # New Enterprise Fields
        applied_coupon_id = data.get('applied_coupon_id')
        discount_amount = data.get('discount_amount', 0)
        points_redeemed = data.get('points_redeemed', 0)
        points_earned = int(float(total_price) / 100) # Earn 1 point per 100 Pesos

        cur = get_cursor()
        
        # Security Check: Ensure user has an approved license
        cur.execute("SELECT is_verified FROM users WHERE id = %s", (user_id,))
        user_row = cur.fetchone()
        if not user_row:
            return jsonify({"error": "User not found"}), 404
            
        is_verified = user_row.get('is_verified')
        if not is_verified or is_verified in [0, False, 'false', '0']:
            return jsonify({
                "error": "License verification required", 
                "message": "Your driver's license must be approved by an administrator before you can book a vehicle."
            }), 403
        
        # Handle Payment Type and Amounts
        payment_type = data.get('payment_type', 'Full')
        
        # Calculate amount paid and balance
        if payment_type == 'Downpayment':
            amount_paid = float(total_price) * 0.20 # 20% downpayment
            balance_amount = float(total_price) - amount_paid
        else:
            amount_paid = float(total_price)
            balance_amount = 0

        # Insert the booking
        cur.execute("""
            INSERT INTO bookings (
                user_id, vehicle_id, driver_id, start_date, end_date,
                pickup_location, rental_type, addons, insurance_type, insurance_price,
                base_price, addon_price, total_price, 
                applied_coupon_id, discount_amount, points_redeemed, points_earned,
                status, payment_type, amount_paid, balance_amount
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            user_id, vehicle_id, driver_id, start_date, end_date,
            pickup_location, rental_type, addons, insurance_type, insurance_price,
            base_price, addon_price, total_price,
            applied_coupon_id, discount_amount, points_redeemed, points_earned,
            'Pending', payment_type, amount_paid, balance_amount
        ))
        
        booking_data = cur.fetchone()
        booking_id = booking_data['id']
        commit_db()
        
        # Send Notification
        send_notification(
            user_id=user_id,
            subject="Booking Received! - Autoride",
            message=f"We have received your booking #{booking_id}. Our team will review it shortly. Thank you!"
        )
        
        print(f"DEBUG: Created booking {booking_id} for user {user_id}")
        return jsonify({
            "message": "Booking created successfully",
            "booking_id": booking_id
        }), 201

    except Exception as e:
        print(f"BOOKING ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500

@booking_bp.route('/api/bookings/<int:booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    """Customer cancels their own booking."""
    try:
        data = request.json
        user_id = data.get('user_id')
        reason = data.get('reason', 'No reason provided')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
            
        cur = get_cursor()
        
        # Verify the booking belongs to the user and is not already completed/cancelled
        cur.execute("SELECT id, status, payment_status, total_price FROM bookings WHERE id = %s AND user_id = %s", (booking_id, user_id))
        booking = cur.fetchone()
        
        if not booking:
            return jsonify({"error": "Booking not found or unauthorized"}), 404
            
        if booking['status'] in ['Completed', 'Cancelled']:
            return jsonify({"error": f"Cannot cancel a {booking['status']} booking"}), 400
            
        # Update booking to Cancelled
        cur.execute("""
            UPDATE bookings 
            SET status = 'Cancelled', 
                cancellation_reason = %s, 
                cancelled_by = 'Customer'
            WHERE id = %s
        """, (reason, booking_id))
        
        # Determine if refund is needed (if they paid something)
        # Note: In real life, downpayments < 48 hours are non-refundable. 
        # For simplicity, if they paid, we set payment_status to 'Refund Pending' or leave it if non-refundable.
        # Let's set it to 'Refund Pending' so admin can review.
        if booking['payment_status'] in ['Paid', 'Partially Paid']:
            cur.execute("UPDATE bookings SET payment_status = 'Refund Pending' WHERE id = %s", (booking_id,))
            
        # Free up the vehicle
        cur.execute("""
            UPDATE vehicles 
            SET status = 'Available' 
            WHERE id = (SELECT vehicle_id FROM bookings WHERE id = %s)
        """, (booking_id,))
        
        commit_db()
        
        # Send Notification
        send_notification(
            user_id=user_id,
            subject="Booking Cancelled",
            message=f"Your booking #{booking_id} has been cancelled successfully. Reason: {reason}"
        )
        
        return jsonify({"message": "Booking cancelled successfully"}), 200
        
    except Exception as e:
        print(f"CANCEL ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500

@booking_bp.route('/api/admin/bookings/<int:booking_id>/mark-paid', methods=['POST'])
def admin_mark_paid(booking_id):
    """Admin marks a partially paid booking as fully paid (Over the counter cash)."""
    try:
        cur = get_cursor()
        
        # Verify booking
        cur.execute("SELECT id, payment_status, balance_amount, amount_paid, total_price FROM bookings WHERE id = %s", (booking_id,))
        booking = cur.fetchone()
        
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
            
        if booking['payment_status'] == 'Paid':
            return jsonify({"error": "Booking is already fully paid."}), 400

        # Create a payment record for the cash transaction
        balance = float(booking['balance_amount'] or 0)
        total = float(booking['total_price'] or 0)
        
        if balance <= 0:
            balance = total - float(booking['amount_paid'] or 0)
            
        cur.execute("""
            INSERT INTO payments (booking_id, amount, method, reference_number, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (booking_id, balance, 'Cash (Over the counter)', f"CASH-{booking_id}", 'Completed'))

        # Update booking amounts and status
        cur.execute("""
            UPDATE bookings 
            SET amount_paid = %s, balance_amount = 0, payment_status = 'Paid'
            WHERE id = %s
        """, (total, booking_id))
        
        commit_db()
        print(f"DEBUG: Admin marked booking {booking_id} as Paid.")
        
        return jsonify({"message": "Booking marked as fully paid successfully."}), 200

    except Exception as e:
        print(f"ADMIN MARK PAID ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500
