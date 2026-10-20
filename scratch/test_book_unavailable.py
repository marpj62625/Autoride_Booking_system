import os, sys
sys.path.insert(0, os.path.abspath('AutorideSystem/backend'))
from app import app

with app.test_client() as client:
    res = client.post('/api/book', json={
        'vehicle_id': 24, # Avanza G (DAO 4897 - Unavailable)
        'user_id': 39,
        'start_date': '2026-11-01',
        'end_date': '2026-11-03',
        'start_time': '09:00',
        'end_time': '09:00',
        'driver_option': 'self_drive',
        'payment_method': 'cash',
        'destination': 'Metro Manila',
        'purpose_of_rental': 'Business'
    })
    print('=== BOOKING REJECTION TEST: Vehicle 24 (Unavailable) ===')
    print('Status code:', res.status_code)
    print('Response:', res.get_json())
