with open('backend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_routes = """
@app.route('/api/admin/bookings/<int:booking_id>/license-details', methods=['GET'])
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

@app.route('/api/admin/users/<int:user_id>/license-details', methods=['GET'])
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
"""

# Insert before the last route or at a known location
idx = content.find("@app.route('/api/user/license-details'")
if idx == -1:
    print("Error finding insertion point")
else:
    # insert before
    content = content[:idx] + new_routes + "\n" + content[idx:]
    with open('backend/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully added new routes to backend/app.py")
