from flask import Blueprint, request, jsonify
from database import get_cursor, commit_db
from services.extension_service import (
    get_alternative_vehicles,
    resolve_conflict_alternative,
    resolve_conflict_refund
)

conflict_bp = Blueprint('conflicts', __name__)

@conflict_bp.route('/api/conflicts/my-affected-bookings', methods=['GET'])
def get_my_affected_bookings():
    # Return bookings affected by extension conflicts
    try:
        user_id = request.args.get('user_id', type=int) # For simplicity, client can pass user_id or authenticate
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
            
        cur = get_cursor()
        cur.execute("""
            SELECT b.*, c.id as conflict_record_id, c.resolution_status, c.resolution_deadline,
                   v.brand, v.model, v.plate_number, v.vehicle_image
            FROM bookings b
            JOIN booking_conflicts c ON c.affected_booking_id = b.id
            JOIN vehicles v ON v.id = b.vehicle_id
            WHERE b.user_id = %s 
              AND b.is_conflict_affected = TRUE
              AND c.resolution_status = 'Pending'
        """, (user_id,))
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            for k in ('start_date', 'end_date', 'resolution_deadline', 'created_at'):
                if d.get(k): d[k] = str(d[k])
            result.append(d)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@conflict_bp.route('/api/conflicts/<int:conflict_id>/alternatives', methods=['GET'])
def get_conflict_alternatives(conflict_id):
    try:
        alternatives = get_alternative_vehicles(conflict_id)
        # Check No Match 🚫 constraint
        if not alternatives:
            return jsonify({
                "alternatives": [],
                "alternatives_available": False,
                "message": "No alternative vehicles available"
            }), 200
            
        return jsonify({
            "alternatives": alternatives,
            "alternatives_available": True
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@conflict_bp.route('/api/conflicts/<int:conflict_id>/select-alternative', methods=['POST'])
def select_alternative(conflict_id):
    try:
        data = request.get_json(silent=True) or {}
        selected_vehicle_id = data.get('selected_vehicle_id')
        if not selected_vehicle_id:
            return jsonify({"error": "selected_vehicle_id is required"}), 400
            
        success = resolve_conflict_alternative(conflict_id, selected_vehicle_id)
        if not success:
            return jsonify({"error": "Selected vehicle is no longer available or conflict already resolved"}), 400
            
        return jsonify({"message": "Vehicle successfully swapped. Conflict resolved."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@conflict_bp.route('/api/conflicts/<int:conflict_id>/refund', methods=['POST'])
def request_conflict_refund(conflict_id):
    try:
        success = resolve_conflict_refund(conflict_id)
        if not success:
            return jsonify({"error": "Conflict already resolved or not found"}), 400
            
        return jsonify({"message": "Booking cancelled. Full refund will be processed immediately."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
