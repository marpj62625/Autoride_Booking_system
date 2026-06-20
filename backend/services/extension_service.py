import datetime
import psycopg
from database import get_connection, release_connection

def _get_cursor():
    from flask import has_app_context
    if has_app_context():
        from database import get_cursor
        return get_cursor(), None
    else:
        from psycopg.rows import dict_row
        conn = get_connection()
        return conn.cursor(row_factory=dict_row), conn

def _commit_and_close(cur, conn):
    if conn:
        conn.commit()
        cur.close()
        conn.close()
    else:
        from database import commit_db
        commit_db()

def _rollback_and_close(cur, conn):
    if conn:
        conn.rollback()
        cur.close()
        conn.close()

def detect_conflicts(booking_id, new_end_date):
    cur, conn = _get_cursor()
    try:
        cur.execute("SELECT vehicle_id, end_date FROM bookings WHERE id = %s", (booking_id,))
        booking = cur.fetchone()
        if not booking:
            return []
        
        vehicle_id = booking['vehicle_id']
        orig_end_date = booking['end_date']
        
        cur.execute("""
            SELECT id, user_id, start_date, end_date, total_price 
            FROM bookings
            WHERE vehicle_id = %s
              AND id != %s
              AND status IN ('Approved', 'Confirmed', 'Picked Up', 'Ongoing', 'Pending')
              AND start_date <= %s
              AND end_date >= %s
        """, (vehicle_id, booking_id, new_end_date, orig_end_date))
        res = cur.fetchall()
        return res
    finally:
        if conn:
            cur.close()
            conn.close()

def get_alternative_vehicles(conflict_id):
    cur, conn = _get_cursor()
    try:
        cur.execute("""
            SELECT c.*, b.vehicle_id as orig_vehicle_id, b.start_date, b.end_date, b.pickup_location
            FROM booking_conflicts c
            JOIN bookings b ON b.id = c.affected_booking_id
            WHERE c.id = %s
        """, (conflict_id,))
        conflict = cur.fetchone()
        if not conflict:
            return []
            
        start_date = conflict['start_date']
        end_date = conflict['end_date']
        pickup_location = conflict['pickup_location']
        orig_vehicle_id = conflict['orig_vehicle_id']
        
        cur.execute("""
            SELECT brand, model, daily_rate, vehicle_type, location 
            FROM vehicles WHERE id = %s
        """, (orig_vehicle_id,))
        orig_car = cur.fetchone()
        if not orig_car:
            return []
            
        brand = orig_car['brand']
        model = orig_car['model']
        daily_rate = float(orig_car['daily_rate'])
        category = orig_car['vehicle_type']
        
        cur.execute("""
            SELECT v.* 
            FROM vehicles v
            WHERE v.status = 'Available'
              AND v.id != %s
              AND v.location = %s
              AND NOT EXISTS (
                  SELECT 1 FROM bookings b
                  WHERE b.vehicle_id = v.id
                    AND b.status IN ('Approved', 'Confirmed', 'Picked Up', 'Ongoing', 'Pending')
                    AND b.start_date <= %s
                    AND b.end_date >= %s
              )
        """, (orig_vehicle_id, pickup_location, end_date, start_date))
        available_vehicles = cur.fetchall()
        
        results = []
        for car in available_vehicles:
            car_rate = float(car['daily_rate'])
            car_brand = car['brand']
            car_category = car['vehicle_type']
            
            tier = None
            if car_brand.lower() == brand.lower() and car_category.lower() == category.lower() and abs(car_rate - daily_rate) <= (0.02 * daily_rate):
                tier = 1
                tier_label = "Perfect Match"
            elif car_category.lower() == category.lower() and (car_brand.lower() == brand.lower() or abs(car_rate - daily_rate) <= (0.05 * daily_rate)):
                tier = 2
                tier_label = "Close Match"
            elif car_category.lower() == category.lower() and abs(car_rate - daily_rate) <= (0.10 * daily_rate):
                tier = 3
                tier_label = "Alternative"
                
            if tier is not None:
                results.append({
                    "vehicle_id": car['id'],
                    "brand": car['brand'],
                    "model": car['model'],
                    "daily_rate": car_rate,
                    "vehicle_type": car['vehicle_type'],
                    "transmission": car['transmission'],
                    "fuel_type": car['fuel_type'],
                    "seats": car['seats'],
                    "vehicle_image": car['vehicle_image'],
                    "tier": tier,
                    "tier_label": tier_label,
                    "price_diff": car_rate - daily_rate
                })
                
        results.sort(key=lambda x: (x['tier'], 0 if x['brand'].lower() == brand.lower() else 1, abs(x['daily_rate'] - daily_rate)))
        return results[:5]
    finally:
        if conn:
            cur.close()
            conn.close()

def resolve_conflict_alternative(conflict_id, selected_vehicle_id):
    cur, conn = _get_cursor()
    try:
        cur.execute("SELECT * FROM booking_conflicts WHERE id = %s", (conflict_id,))
        conflict = cur.fetchone()
        if not conflict or conflict['resolution_status'] != 'Pending':
            return False
            
        cur.execute("""
            SELECT 1 FROM bookings 
            WHERE vehicle_id = %s
              AND status IN ('Approved', 'Confirmed', 'Picked Up', 'Ongoing', 'Pending')
              AND start_date <= %s
              AND end_date >= %s
        """, (selected_vehicle_id, conflict['conflict_end_date'], conflict['conflict_start_date']))
        if cur.fetchone():
            return False
            
        cur.execute("""
            UPDATE bookings 
            SET vehicle_id = %s, is_conflict_affected = FALSE, conflict_id = NULL 
            WHERE id = %s
        """, (selected_vehicle_id, conflict['affected_booking_id']))
        
        cur.execute("""
            UPDATE booking_conflicts 
            SET resolution_status = 'Resolved - Swapped', selected_alternative_vehicle_id = %s, customer_responded_at = NOW(), updated_at = NOW()
            WHERE id = %s
        """, (selected_vehicle_id, conflict_id))
        
        _commit_and_close(cur, conn)
        return True
    except Exception as e:
        _rollback_and_close(cur, conn)
        raise e

def resolve_conflict_refund(conflict_id):
    cur, conn = _get_cursor()
    try:
        cur.execute("SELECT * FROM booking_conflicts WHERE id = %s", (conflict_id,))
        conflict = cur.fetchone()
        if not conflict or conflict['resolution_status'] != 'Pending':
            return False
            
        cur.execute("""
            UPDATE bookings 
            SET status = 'Cancelled', payment_status = 'Refund Pending', is_conflict_affected = FALSE, conflict_id = NULL 
            WHERE id = %s
        """, (conflict['affected_booking_id'],))
        
        cur.execute("SELECT total_price FROM bookings WHERE id = %s", (conflict['affected_booking_id'],))
        b = cur.fetchone()
        refund_amount = b['total_price'] if b else 0
        
        cur.execute("""
            UPDATE booking_conflicts 
            SET resolution_status = 'Resolved - Refunded', refund_amount = %s, refund_status = 'Pending', customer_responded_at = NOW(), updated_at = NOW()
            WHERE id = %s
        """, (refund_amount, conflict_id))
        
        _commit_and_close(cur, conn)
        return True
    except Exception as e:
        _rollback_and_close(cur, conn)
        raise e

def check_expired_deadlines():
    cur, conn = _get_cursor()
    try:
        cur.execute("""
            SELECT id FROM booking_conflicts 
            WHERE resolution_status = 'Pending' 
              AND resolution_deadline < NOW()
        """)
        expired = cur.fetchall()
        for exp in expired:
            resolve_conflict_refund(exp['id'])
            
            try:
                from notifications import notification_service
                cur.execute("""
                    SELECT affected_user_id, affected_booking_id 
                    FROM booking_conflicts WHERE id = %s
                """, (exp['id'],))
                c = cur.fetchone()
                if c:
                    notification_service.notify_user(c['affected_user_id'], "Booking Auto-Cancelled",
                        f"Your booking #{c['affected_booking_id']} was auto-cancelled because the resolution deadline passed. "
                        f"A full refund has been initiated.",
                        'booking_autocancelled')
            except Exception:
                pass
        _commit_and_close(cur, conn)
    except Exception as e:
        _rollback_and_close(cur, conn)
        print("Error checking expired deadlines:", e)
