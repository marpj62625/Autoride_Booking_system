import sys, os, datetime
sys.path.append(os.path.abspath('backend'))
from database import get_connection
from psycopg.rows import dict_row

conn = get_connection()
conn.autocommit = False
cur = conn.cursor(row_factory=dict_row)

user_ids = [25, 26, 27, 28, 29, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48]
cur.execute("SELECT id, full_name, phone, email FROM users WHERE id = ANY(%s)", (user_ids,))
users = {u['id']: u for u in cur.fetchall()}

cur.execute("SELECT id, brand, model, plate_number FROM vehicles")
vehicles = {v['id']: v for v in cur.fetchall()}

def get_veh_by_plate(plate_sub):
    for vid, v in vehicles.items():
        if plate_sub.replace(' ', '').lower() in v['plate_number'].replace(' ', '').lower():
            return v
    return None

def get_color(name):
    palette = ['#fde047', '#86efac', '#93c5fd', '#fdba74', '#d8b4fe', '#fca5a5', '#f472b6', '#5eead4', '#fde68a', '#c7d2fe', '#bef264', '#67e8f9']
    hash_val = sum(ord(c) for c in name.lower().strip()) % len(palette)
    return palette[hash_val]

# The 13 exact conflict-free allocations
alloc_items = [
    {
        'user_id': 27, # Allan Jr. Tan Anas
        'veh_plate': 'DAT 1396',
        'start_date': datetime.date(2026, 10, 1),
        'end_date': datetime.date(2026, 10, 1),
        'orig_cust': 'JOSH YOUAYN MALLARI',
        'rate': 1800.0,
    },
    {
        'user_id': 29, # Julius Sensida Labrador
        'veh_plate': 'CCK 1126',
        'start_date': datetime.date(2026, 10, 1),
        'end_date': datetime.date(2026, 10, 30),
        'orig_cust': 'MERRY JOY TORRES',
        'rate': 75000.0, # 30 days @ 2500
    },
    {
        'user_id': 38, # Arl Junell Ramos Tobias
        'veh_plate': 'NID 2724',
        'start_date': datetime.date(2026, 10, 6),
        'end_date': datetime.date(2026, 10, 13),
        'orig_cust': 'JOEM MARK REYES BULOTANO',
        'rate': 20800.0, # 8 days @ 2600
    },
    {
        'user_id': 41, # Danny Lastra Calix
        'veh_plate': 'NHN 5388',
        'start_date': datetime.date(2026, 10, 6),
        'end_date': datetime.date(2026, 10, 8),
        'orig_cust': 'JAY KARL GONZALES',
        'rate': 7500.0, # 3 days @ 2500
    },
    {
        'user_id': 42, # John Robin Castillo Uri
        'veh_plate': 'DAT 1396',
        'start_date': datetime.date(2026, 10, 10),
        'end_date': datetime.date(2026, 10, 11),
        'orig_cust': 'JAYMIE CACHERO',
        'rate': 3600.0, # 2 days @ 1800
    },
    {
        'user_id': 43, # Mike Handomon
        'veh_plate': 'DAT 1396',
        'start_date': datetime.date(2026, 10, 12),
        'end_date': datetime.date(2026, 10, 17),
        'orig_cust': 'SHARMAINE BERNABE RUTAQUIO',
        'rate': 10800.0, # 6 days @ 1800
    },
    {
        'user_id': 44, # Eliezer Cadarit Amador
        'veh_plate': 'NHN 5388',
        'start_date': datetime.date(2026, 10, 12),
        'end_date': datetime.date(2026, 10, 19),
        'orig_cust': 'SUNLINE ELECTRONICS',
        'rate': 20000.0, # 8 days @ 2500
    },
    {
        'user_id': 25, # Guamil Gabriel Delos Reyes Sanchez
        'veh_plate': 'NCX 4117',
        'start_date': datetime.date(2026, 10, 14),
        'end_date': datetime.date(2026, 10, 14),
        'orig_cust': 'JESTONI CHRISTIAN PASCO',
        'rate': 1500.0,
    },
    {
        'user_id': 26, # Michael Ortega Jarina
        'veh_plate': 'DBJ 9483',
        'start_date': datetime.date(2026, 10, 15),
        'end_date': datetime.date(2026, 10, 16),
        'orig_cust': 'GOMER MERCADO',
        'rate': 3600.0, # 2 days @ 1800
    },
    {
        'user_id': 28, # Villy Sepuesca Arroz
        'veh_plate': 'NCX 4117',
        'start_date': datetime.date(2026, 10, 30),
        'end_date': datetime.date(2026, 10, 30),
        'orig_cust': 'KHYM CRUZ - SANCHEZ',
        'rate': 1500.0,
    },
    {
        'user_id': 39, # Rolly Corton Pelicano
        'veh_plate': 'NCX 4117',
        'start_date': datetime.date(2026, 11, 1),
        'end_date': datetime.date(2026, 11, 2),
        'orig_cust': 'HUBBERT SANCHEZ',
        'rate': 3000.0, # 2 days @ 1500
    },
    {
        'user_id': 40, # Vicmar Goloran Alquino
        'veh_plate': 'NCX 4117',
        'start_date': datetime.date(2026, 12, 9),
        'end_date': datetime.date(2026, 12, 10),
        'orig_cust': 'MICHAELLA ANGELA TABLASON',
        'rate': 3000.0, # 2 days @ 1500
    },
    {
        'user_id': 46, # Virgilio Gonzales Oña
        'veh_plate': 'NHN 5388',
        'start_date': datetime.date(2026, 12, 23),
        'end_date': datetime.date(2026, 12, 29),
        'orig_cust': 'JAY-AR CABILES',
        'rate': 17500.0, # 7 days @ 2500
    }
]

created_ids = []

try:
    for item in alloc_items:
        u = users[item['user_id']]
        v = get_veh_by_plate(item['veh_plate'])
        assert v is not None, f"Vehicle not found for plate {item['veh_plate']}"

        color = get_color(u['full_name'])
        phone = u['phone'] or '09171234567'

        cur.execute("""
            INSERT INTO bookings (
                vehicle_id, user_id, customer_name, customer_phone,
                start_date, end_date, start_time, end_time,
                total_price, base_price, amount_paid, balance_amount,
                status, payment_status, payment_method, service_type, rental_type,
                calendar_color, pickup_location, destination, created_at
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, '09:00', '17:00',
                %s, %s, %s, 0.00,
                'confirmed', 'Paid', 'Cash', 'self-drive', 'daily',
                %s, 'Office / Garage', 'Local Tour', NOW()
            ) RETURNING id
        """, (
            v['id'], u['id'], u['full_name'], phone,
            item['start_date'], item['end_date'],
            item['rate'], item['rate'], item['rate'],
            color
        ))
        new_id = cur.fetchone()['id']
        created_ids.append(new_id)
        print(f"INSERTED Booking #{new_id}: User #{u['id']} ({u['full_name']}) | {v['brand']} {v['model']} [{v['plate_number']}] | {item['start_date']} to {item['end_date']} | Rate: {item['rate']} (Orig: {item['orig_cust']})")

    conn.commit()
    print(f"\nSUCCESS: All {len(created_ids)} bookings committed to database cleanly!")
except Exception as e:
    conn.rollback()
    print("ERROR occurred during insertion, rolled back:", e)
finally:
    conn.close()
