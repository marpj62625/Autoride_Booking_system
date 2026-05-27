@app.route('/api/user/license-details', methods=['GET'])
def get_license_details():
    """Get the full driver's license details for a user."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        cur = get_cursor()
        cur.execute(
            """SELECT * FROM license_details WHERE user_id = %s""",
            (user_id,)
        )
        row = cur.fetchone()
        if row:
            d = dict_row(cur).load(row)
            # convert dates to string
            if d.get('date_of_birth'): d['date_of_birth'] = str(d['date_of_birth'])
            if d.get('expiry_date'): d['expiry_date'] = str(d['expiry_date'])
            if d.get('created_at'): d['created_at'] = str(d['created_at'])
            if d.get('updated_at'): d['updated_at'] = str(d['updated_at'])
            return jsonify(d), 200
        else:
            return jsonify({}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

@app.route('/api/user/license-details', methods=['POST'])
def save_license_details():
    """Save or update full driver's license details."""
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        cur = get_cursor()
        
        full_name = request.form.get('full_name', '')
        date_of_birth = request.form.get('date_of_birth', '')
        license_number = request.form.get('license_number', '')
        expiry_date = request.form.get('expiry_date', '')
        issuing_country_state = request.form.get('issuing_country_state', '')
        license_class = request.form.get('license_class', '')
        emergency_contact_name = request.form.get('emergency_contact_name', '')
        emergency_contact_phone = request.form.get('emergency_contact_phone', '')
        emergency_contact_relationship = request.form.get('emergency_contact_relationship', '')
        
        front_url = request.form.get('license_front_url', '')
        back_url = request.form.get('license_back_url', '')

        # handle file uploads if present
        def upload_img(file_key, prefix):
            if file_key in request.files and request.files[file_key].filename:
                file = request.files[file_key]
                filename = f"{prefix}_{user_id}_{int(datetime.now().timestamp())}.jpg"
                file_data = file.read()
                try:
                    supabase.storage.from_('uploads').upload(path=filename, file=file_data, file_options={"content-type": "image/jpeg", "upsert": "true"})
                except Exception:
                    supabase.storage.from_('uploads').update(path=filename, file=file_data, file_options={"content-type": "image/jpeg"})
                return supabase.storage.from_('uploads').get_public_url(filename)
            return None

        new_front = upload_img('license_front_file', 'license_front')
        if new_front: front_url = new_front
        
        new_back = upload_img('license_back_file', 'license_back')
        if new_back: back_url = new_back

        cur.execute("SELECT id FROM license_details WHERE user_id = %s", (user_id,))
        exists = cur.fetchone()

        if exists:
            cur.execute("""
                UPDATE license_details SET
                    full_name=%s, date_of_birth=%s, license_number=%s, expiry_date=%s,
                    issuing_country_state=%s, license_class=%s, emergency_contact_name=%s,
                    emergency_contact_phone=%s, emergency_contact_relationship=%s,
                    license_front_url=%s, license_back_url=%s, updated_at=CURRENT_TIMESTAMP
                WHERE user_id=%s
            """, (full_name, date_of_birth, license_number, expiry_date, issuing_country_state, license_class, emergency_contact_name, emergency_contact_phone, emergency_contact_relationship, front_url, back_url, user_id))
        else:
            cur.execute("""
                INSERT INTO license_details (
                    user_id, full_name, date_of_birth, license_number, expiry_date,
                    issuing_country_state, license_class, emergency_contact_name,
                    emergency_contact_phone, emergency_contact_relationship,
                    license_front_url, license_back_url
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, full_name, date_of_birth, license_number, expiry_date, issuing_country_state, license_class, emergency_contact_name, emergency_contact_phone, emergency_contact_relationship, front_url, back_url))
            
        commit_db()
        return jsonify({'message': 'License details saved successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()

