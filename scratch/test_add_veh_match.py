with open('backend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''@app.route('/api/vehicles', methods=['POST'])
def add_vehicle():
    # Support both JSON and FormData
    if request.is_json:
        data = request.json
    else:
        data = request.form
    try:
        cur = get_cursor()
        # Ensure vehicle monitoring columns exist
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS color VARCHAR(50) DEFAULT NULL")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS mileage_type VARCHAR(20) DEFAULT 'limited'")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS mileage_km_per_day INT DEFAULT 250")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS year_model INT DEFAULT NULL")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS odometer INT DEFAULT 0")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS fuel_level VARCHAR(20) DEFAULT 'Full Tank'")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS next_service_schedule DATE DEFAULT NULL")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS lto_expiry_date DATE DEFAULT NULL")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS gps_device_token TEXT DEFAULT NULL")
        cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS gps_device_name VARCHAR(100) DEFAULT NULL")
        
        color = data.get('color') or None'''

cnt = content.count(target)
print("Match count for add_vehicle target:", cnt)
