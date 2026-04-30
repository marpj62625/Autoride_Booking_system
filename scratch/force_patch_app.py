import sys

file_path = r"c:\Users\patri\OneDrive\Desktop\AutorideSystem2side\AutorideSystem\backend\app.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define the exact block to replace
old_block = """@app.route('/vehicles', methods=['GET'])
def get_vehicles():
    user_id = request.args.get('user_id')
    favorites_only = request.args.get('favorites_only') == 'true'
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        cur = get_cursor()
        
        if favorites_only and user_id and user_id != 'null':
            query = \"\"\"
                SELECT v.* FROM vehicles v
                JOIN favorites f ON v.id = f.vehicle_id
                WHERE f.user_id = %s
            \"\"\"
            params = [user_id]
            cur.execute(query, params)
        else:
            query = \"SELECT * FROM vehicles v WHERE 1=1\"
            params = []
            cur.execute(query, params)
            
        vehicles = cur.fetchall()
        result = [dict(v) for v in vehicles]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({\"error\": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()"""

new_block = """@app.route('/vehicles', methods=['GET'])
def get_vehicles():
    user_id = request.args.get('user_id')
    favorites_only = request.args.get('favorites_only') == 'true'
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        cur = get_cursor()
        
        # Base query logic
        if favorites_only and user_id and user_id != 'null':
            query = \"\"\"
                SELECT v.* FROM vehicles v
                JOIN favorites f ON v.id = f.vehicle_id
                WHERE f.user_id = %s
            \"\"\"
            params = [user_id]
        else:
            query = \"SELECT * FROM vehicles v WHERE 1=1\"
            params = []

        # Add Date Availability Logic
        if start_date and end_date:
            query += \"\"\"
                AND NOT EXISTS (
                    SELECT 1 FROM bookings b
                    WHERE b.vehicle_id = v.id
                    AND b.status IN ('Confirmed', 'Pending')
                    AND (%s <= b.end_date AND %s >= b.start_date)
                )
            \"\"\"
            params.extend([start_date, end_date])
            
        cur.execute(query, params)
        vehicles = cur.fetchall()
        result = [dict(v) for v in vehicles]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({\"error\": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()"""

# Try direct replacement
if old_block in content:
    content = content.replace(old_block, new_block)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Direct match found and replaced.")
else:
    # Try with line-by-line normalization (ignoring CRLF differences)
    old_lines = old_block.splitlines()
    content_lines = content.splitlines()
    
    found = False
    for i in range(len(content_lines) - len(old_lines) + 1):
        match = True
        for j in range(len(old_lines)):
            if content_lines[i+j].strip() != old_lines[j].strip():
                match = False
                break
        if match:
            # Replace
            new_content_lines = content_lines[:i] + new_block.splitlines() + content_lines[i+len(old_lines):]
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("\\n".join(new_content_lines))
            print(f"Match found by normalization at line {i+1} and replaced.")
            found = True
            break
    
    if not found:
        print("Block not found even with normalization.")
