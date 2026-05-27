import sys, os
sys.path.append('C:/Users/patri/OneDrive/Desktop/AutorideSystem2sides/AutorideSystem/backend')
from app import get_cursor
try:
    cur = get_cursor()
    cur.execute('''
        SELECT v.brand, v.model, v.plate_number,
               COUNT(b.id) as booking_count,
               COALESCE(SUM(b.total_price), 0) as revenue
        FROM vehicles v
        LEFT JOIN bookings b ON b.vehicle_id = v.id AND b.payment_status = 'Paid'
        GROUP BY v.id, v.brand, v.model, v.plate_number
        ORDER BY revenue DESC
        LIMIT 5
    ''')
    rows = cur.fetchall()
    print('Rows:', rows)
    top_vehicles = [{'brand': r['brand'], 'model': r['model'], 'booking_count': int(r['booking_count']), 'revenue': float(r['revenue'])} for r in rows]
    print('top_vehicles:', top_vehicles)
except Exception as e:
    import traceback
    traceback.print_exc()
