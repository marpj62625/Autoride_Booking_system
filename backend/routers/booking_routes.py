from flask import Blueprint, request, jsonify
from database import get_cursor, commit_db
import json
from notifications import notification_service

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
        base_price = data.get('base_price', 0)
        addon_price = data.get('addon_price', 0)
        total_price = data.get('total_price', 0)
        addons = json.dumps(data.get('addons', []))
        insurance_type = data.get('insurance_type', 'Basic')
        insurance_price = data.get('insurance_price', 0)
        applied_coupon_id = data.get('applied_coupon_id')
        discount_amount = data.get('discount_amount', 0)
        points_redeemed = data.get('points_redeemed', 0)
        points_earned = int(float(total_price) / 100)
        
        start_time = data.get('pickup_time', '06:00')
        end_time = data.get('return_time', '06:00')
        service_type = data.get('service_type', 'pickup')
        
        pickup_province = data.get('pickup_province')
        pickup_municipality = data.get('pickup_municipality')
        pickup_barangay = data.get('pickup_barangay')
        return_province = data.get('return_province')
        return_municipality = data.get('return_municipality')
        return_barangay = data.get('return_barangay')

        cur = get_cursor()

        # Security Check: Ensure user has an approved license
        cur.execute("SELECT is_verified FROM users WHERE id = %s", (user_id,))
        verify_row = cur.fetchone()
        if not verify_row:
            return jsonify({"error": "User not found"}), 404

        is_user_verified = verify_row.get('is_verified')
        if not is_user_verified or is_user_verified in [0, False, 'false', '0']:
            return jsonify({
                "error": "License verification required",
                "message": "Your driver's license must be approved by an administrator before you can book a vehicle."
            }), 403

        # Check for blackout dates
        cur.execute("""
            SELECT id, reason, affected_vehicles 
            FROM blackout_dates 
            WHERE start_date <= %s AND end_date >= %s
        """, (end_date, start_date))
        blackouts = cur.fetchall()
        for b in blackouts:
            if not b.get('affected_vehicles') or b['affected_vehicles'] == 'all':
                return jsonify({
                    "error": "Blackout Date Conflict",
                    "message": f"Ang petsa na ito ay hindi available: {b['reason']}"
                }), 409
            affected = [v.strip() for v in b['affected_vehicles'].split(',')]
            if str(vehicle_id) in affected:
                return jsonify({
                    "error": "Blackout Date Conflict",
                    "message": f"Ang sasakyang ito ay hindi available: {b['reason']}"
                }), 409

        # Check for overlapping active bookings for this vehicle
        cur.execute("""
            SELECT COUNT(*) as conflict_count 
            FROM bookings 
            WHERE vehicle_id = %s 
              AND status IN ('Pending', 'Confirmed', 'Approved', 'Picked Up', 'Ongoing')
              AND start_date <= %s 
              AND end_date >= %s
        """, (vehicle_id, end_date, start_date))
        conflict = cur.fetchone()
        if conflict and conflict.get('conflict_count', 0) > 0:
            return jsonify({
                "error": "Vehicle Unavailable",
                "message": "Ang sasakyan ay mayroon nang booking sa napiling mga petsa. Mangyaring pumili ng ibang petsa o ibang sasakyan."
            }), 400

        payment_type = data.get('payment_type', 'Full')
        if payment_type == 'Downpayment':
            amount_paid = float(total_price) * 0.20
            balance_amount = float(total_price) - amount_paid
        else:
            amount_paid = float(total_price)
            balance_amount = 0

        cur.execute("""
            INSERT INTO bookings (
                user_id, vehicle_id, start_date, end_date,
                pickup_location, rental_type, addons, insurance_type, insurance_price,
                base_price, addon_price, total_price,
                applied_coupon_id, discount_amount, points_redeemed, points_earned,
                status, payment_type, amount_paid, balance_amount,
                start_time, end_time, service_type,
                pickup_province, pickup_municipality, pickup_barangay,
                return_province, return_municipality, return_barangay
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            user_id, vehicle_id, start_date, end_date,
            pickup_location, rental_type, addons, insurance_type, insurance_price,
            base_price, addon_price, total_price,
            applied_coupon_id, discount_amount, points_redeemed, points_earned,
            'Pending', payment_type, amount_paid, balance_amount,
            start_time, end_time, service_type,
            pickup_province, pickup_municipality, pickup_barangay,
            return_province, return_municipality, return_barangay
        ))

        booking_data = cur.fetchone()
        booking_id = booking_data['id']
        commit_db()

        # Fetch vehicle and customer info for notifications
        cur.execute("SELECT brand, model FROM vehicles WHERE id = %s", (vehicle_id,))
        vehicle_row = cur.fetchone()
        brand = vehicle_row['brand'] if vehicle_row else 'Unknown'
        model = vehicle_row['model'] if vehicle_row else 'Vehicle'

        cur.execute("SELECT full_name FROM users WHERE id = %s", (user_id,))
        user_row = cur.fetchone()
        customer_name = user_row['full_name'] if user_row else 'Customer'

        # In-app notification to customer
        try:
            notification_service.notify_user(
                user_id,
                "Booking Received",
                f"Your booking #{booking_id} for {brand} {model} from {start_date} to {end_date} has been received. Total: PHP {total_price}.",
                'booking_created'
            )
        except Exception as e:
            print(f"DEBUG: notify_user failed: {e}")

        # In-app notification to all admins
        try:
            notification_service.notify_admins_inapp(
                "New Booking",
                f"New booking #{booking_id} from {customer_name} for {brand} {model}, {start_date} to {end_date}.",
                'admin_new_booking',
                type='admin_new_booking',
                booking_id=booking_id
            )
            print(f"DEBUG: notify_admins_inapp done for booking {booking_id}")
        except Exception as e:
            print(f"DEBUG: notify_admins_inapp failed: {e}")

        print(f"DEBUG: Created booking {booking_id} for user {user_id}")
        return jsonify({
            "message": "Booking created successfully",
            "booking_id": booking_id
        }), 201

    except Exception as e:
        print(f"BOOKING ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500


@booking_bp.route('/bookings/<int:booking_id>/update-price', methods=['POST'])
def update_booking_price(booking_id):
    """Update a pending booking's addons and pricing before payment is finalized."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing data"}), 400

        addons = json.dumps(data.get('addons', []))
        addon_price = data.get('addon_price', 0)
        total_price = data.get('total_price', 0)
        amount_paid = data.get('amount_paid', 0)
        balance_amount = data.get('balance_amount', 0)

        cur = get_cursor()
        cur.execute("SELECT status FROM bookings WHERE id = %s", (booking_id,))
        booking = cur.fetchone()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        cur.execute("""
            UPDATE bookings
            SET addons = %s, addon_price = %s, total_price = %s,
                amount_paid = %s, balance_amount = %s
            WHERE id = %s
        """, (addons, addon_price, total_price, amount_paid, balance_amount, booking_id))

        commit_db()
        return jsonify({"message": "Booking price updated successfully"}), 200

    except Exception as e:
        print(f"UPDATE PRICE ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500


@booking_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    """Customer cancels their own booking."""
    try:
        data = request.json
        user_id = data.get('user_id')
        reason = data.get('reason', 'No reason provided')

        if not user_id:
            return jsonify({"error": "User ID required"}), 400

        cur = get_cursor()
        cur.execute("SELECT id, status, payment_status, total_price, user_id FROM bookings WHERE id = %s AND user_id = %s", (booking_id, user_id))
        booking = cur.fetchone()

        if not booking:
            return jsonify({"error": "Booking not found or unauthorized"}), 404

        if booking['status'] in ['Completed', 'Cancelled']:
            return jsonify({"error": f"Cannot cancel a {booking['status']} booking"}), 400

        cur.execute("""
            UPDATE bookings
            SET status = 'Cancelled', cancellation_reason = %s, cancelled_by = 'Customer'
            WHERE id = %s
        """, (reason, booking_id))

        if booking['payment_status'] in ['Paid', 'Partially Paid']:
            cur.execute("UPDATE bookings SET payment_status = 'Refund Pending' WHERE id = %s", (booking_id,))

        cur.execute("""
            UPDATE vehicles SET status = 'Available'
            WHERE id = (SELECT vehicle_id FROM bookings WHERE id = %s)
        """, (booking_id,))

        commit_db()

        # In-app notification to customer
        try:
            notification_service.notify_user(
                booking['user_id'],
                "Booking Cancelled",
                f"Your booking #{booking_id} has been cancelled. Reason: {reason}.",
                'booking_cancelled'
            )
        except Exception as e:
            print(f"DEBUG: notify_user cancel failed: {e}")

        # In-app notification to admins
        try:
            notification_service.notify_admins_inapp(
                "Booking Cancelled by Customer",
                f"Booking #{booking_id} was cancelled by the customer. Reason: {reason}.",
                'admin_booking_cancelled',
                type='admin_booking_cancelled',
                booking_id=booking_id
            )
        except Exception as e:
            print(f"DEBUG: notify_admins_inapp cancel failed: {e}")

        # If booking is now Refund Pending, also trigger a refund request notification to admins
        if booking['payment_status'] in ['Paid', 'Partially Paid']:
            try:
                notification_service.notify_admins_inapp(
                    "Refund Request",
                    f"Refund request for cancelled booking #{booking_id} by {booking.get('customer_name', 'Customer') or 'Customer'}.",
                    'admin_refund_request',
                    type='admin_refund_request',
                    booking_id=booking_id
                )
            except Exception as e:
                print(f"DEBUG: notify_admins_inapp refund request failed: {e}")

        return jsonify({"message": "Booking cancelled successfully"}), 200

    except Exception as e:
        print(f"CANCEL ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500


@booking_bp.route('/admin/bookings/<int:booking_id>/mark-paid', methods=['POST'])
def admin_mark_paid(booking_id):
    """Admin marks a partially paid booking as fully paid (Over the counter cash)."""
    try:
        cur = get_cursor()
        cur.execute("SELECT id, payment_status, balance_amount, amount_paid, total_price FROM bookings WHERE id = %s", (booking_id,))
        booking = cur.fetchone()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        if booking['payment_status'] == 'Paid':
            return jsonify({"error": "Booking is already fully paid."}), 400

        balance = float(booking['balance_amount'] or 0)
        total = float(booking['total_price'] or 0)
        if balance <= 0:
            balance = total - float(booking['amount_paid'] or 0)

        cur.execute("""
            INSERT INTO payments (booking_id, amount, method, reference_number, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (booking_id, balance, 'Cash (Over the counter)', f"CASH-{booking_id}", 'Completed'))

        cur.execute("""
            UPDATE bookings SET amount_paid = %s, balance_amount = 0, payment_status = 'Paid'
            WHERE id = %s
        """, (total, booking_id))

        commit_db()
        print(f"DEBUG: Admin marked booking {booking_id} as Paid.")

        # In-app notification to customer
        try:
            cur.execute("SELECT user_id FROM bookings WHERE id = %s", (booking_id,))
            bk_row = cur.fetchone()
            if bk_row:
                notification_service.notify_user(
                    bk_row['user_id'],
                    "Payment Confirmed",
                    f"Your booking #{booking_id} has been marked as fully paid. Total: PHP {total}.",
                    'payment_cash'
                )
        except Exception as e:
            print(f"DEBUG: notify_user mark-paid failed: {e}")

        return jsonify({"message": "Booking marked as fully paid successfully."}), 200

    except Exception as e:
        print(f"ADMIN MARK PAID ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500


@booking_bp.route('/bookings/<int:booking_id>/mark-no-show', methods=['POST'])
def mark_no_show(booking_id):
    """Mark a booking as No Show."""
    try:
        cur = get_cursor()
        cur.execute("SELECT id, status, payment_status, user_id, total_price, vehicle_id FROM bookings WHERE id = %s", (booking_id,))
        booking = cur.fetchone()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        # Update booking status to 'No Show'
        # If paid/partially paid, the payment is forfeited (keep amount_paid, but status is No Show)
        # If unpaid, it's just marked as No Show
        cur.execute("""
            UPDATE bookings
            SET status = 'No Show'
            WHERE id = %s
        """, (booking_id,))

        # Free the vehicle
        cur.execute("""
            UPDATE vehicles
            SET status = 'Available'
            WHERE id = %s
        """, (booking['vehicle_id'],))

        commit_db()

        # Notify customer
        try:
            notification_service.notify_user(
                booking['user_id'],
                "Booking Marked as No Show",
                f"Your booking #{booking_id} was marked as No Show because you did not arrive for pickup.",
                'booking_no_show'
            )
        except Exception as e:
            print(f"DEBUG: notify_user no-show failed: {e}")

        return jsonify({"message": "Booking marked as No Show successfully"}), 200

    except Exception as e:
        print(f"MARK NO SHOW ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500


@booking_bp.route('/bookings/past', methods=['GET'])
def get_past_bookings():
    """Fetch past/completed bookings with pagination and sorting."""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        sort_by = request.args.get('sort_by', 'completion_date_desc')

        if page_size not in [10, 25, 50, 100]:
            page_size = 10
        if page < 1:
            page = 1

        offset = (page - 1) * page_size
        sort_column = 'b.end_date'
        sort_order = 'DESC'

        if sort_by == 'completion_date_asc':
            sort_column, sort_order = 'b.end_date', 'ASC'
        elif sort_by == 'customer_name':
            sort_column, sort_order = 'u.full_name', 'ASC'
        elif sort_by == 'total_price_desc':
            sort_column, sort_order = 'b.total_price', 'DESC'
        elif sort_by == 'total_price_asc':
            sort_column, sort_order = 'b.total_price', 'ASC'

        cur = get_cursor()
        cur.execute("SELECT COUNT(*) as total FROM bookings b WHERE b.status = 'Completed' AND COALESCE(b.is_archived, FALSE) = FALSE")
        total_count = cur.fetchone()['total']
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

        query = f"""
            SELECT b.id, b.user_id, u.full_name as customer_name,
                   CONCAT(v.brand, ' ', v.model) as car,
                   b.start_date, b.end_date, b.total_price,
                   b.end_date as completion_date, b.status, b.payment_status
            FROM bookings b
            LEFT JOIN users u ON b.user_id = u.id
            LEFT JOIN vehicles v ON b.vehicle_id = v.id
            WHERE b.status = 'Completed' AND COALESCE(b.is_archived, FALSE) = FALSE
            ORDER BY {sort_column} {sort_order}
            LIMIT %s OFFSET %s
        """
        cur.execute(query, (page_size, offset))
        bookings = cur.fetchall()

        return jsonify({
            "bookings": bookings,
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": total_pages
        }), 200

    except Exception as e:
        print(f"GET PAST BOOKINGS ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500
