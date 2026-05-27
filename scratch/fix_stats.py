import re

with open('C:/Users/patri/OneDrive/Desktop/AutorideSystem2sides/AutorideSystem/backend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """        # Top grossing vehicles
        try:
            cur.execute(\"\"\"
                SELECT v.brand, v.model, v.plate_number,
                       COUNT(b.id) as booking_count,
                       COALESCE(SUM(b.total_price), 0) as revenue
                FROM vehicles v
                LEFT JOIN bookings b ON b.vehicle_id = v.id AND b.payment_status = 'Paid'
                GROUP BY v.id, v.brand, v.model, v.plate_number
                ORDER BY revenue DESC
                LIMIT 5
            \"\"\")
            top_vehicles = [{"brand": r['brand'], "model": r['model'], "booking_count": int(r['booking_count']), "revenue": float(r['revenue'])} for r in cur.fetchall()]
        except Exception:
            top_vehicles = []"""

new_code = """        # Top grossing vehicles
        try:
            cur.execute(\"\"\"
                SELECT v.brand, v.model, v.plate_number,
                       COUNT(b.id) as booking_count,
                       COALESCE(SUM(b.total_price), 0) as revenue
                FROM vehicles v
                LEFT JOIN bookings b ON b.vehicle_id = v.id AND b.payment_status = 'Paid'
                GROUP BY v.id, v.brand, v.model, v.plate_number
                ORDER BY revenue DESC
                LIMIT 5
            \"\"\")
            top_vehicles = [{"brand": r.get('brand'), "model": r.get('model'), "booking_count": int(r.get('booking_count') or 0), "revenue": float(r.get('revenue') or 0)} for r in cur.fetchall()]
        except Exception as e:
            print("ERROR in Top grossing vehicles query:", e)
            top_vehicles = []"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('C:/Users/patri/OneDrive/Desktop/AutorideSystem2sides/AutorideSystem/backend/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced successfully!")
else:
    print("Could not find old code in app.py")
