import re

with open('backend/routers/booking_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

update_route = '''
@booking_bp.route('/bookings/<int:booking_id>/update-price', methods=['POST'])
def update_booking_price(booking_id):
    """Update a pending booking's addons and pricing before payment is finalized."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing data"}), 400
            
        import json
        addons = json.dumps(data.get('addons', []))
        addon_price = data.get('addon_price', 0)
        total_price = data.get('total_price', 0)
        amount_paid = data.get('amount_paid', 0)
        balance_amount = data.get('balance_amount', 0)
        
        cur = get_cursor()
        
        # Verify booking is still Pending
        cur.execute("SELECT status FROM bookings WHERE id = %s", (booking_id,))
        booking = cur.fetchone()
        
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
            
        # Optional: We allow update even if not Pending just in case, but usually only before payment
        
        cur.execute("""
            UPDATE bookings 
            SET addons = %s,
                addon_price = %s,
                total_price = %s,
                amount_paid = %s,
                balance_amount = %s
            WHERE id = %s
        """, (addons, addon_price, total_price, amount_paid, balance_amount, booking_id))
        
        commit_db()
        return jsonify({"message": "Booking price updated successfully"}), 200
        
    except Exception as e:
        print(f"UPDATE PRICE ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500
'''

if 'update_booking_price' not in content:
    # Insert it right before cancel_booking
    content = content.replace('@booking_bp.route(\'/bookings/<int:booking_id>/cancel\', methods=[\'POST\'])', update_route + '\n@booking_bp.route(\'/bookings/<int:booking_id>/cancel\', methods=[\'POST\'])')
    
    with open('backend/routers/booking_routes.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Done backend updates')
else:
    print('Backend route already exists')
