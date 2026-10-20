import os, sys
sys.path.insert(0, os.path.abspath('AutorideSystem/backend'))
from app import app

with app.test_client() as client:
    # 1. Test Categories
    res = client.get('/api/vehicles/categories')
    cats = res.get_json()
    print('=== CATEGORIES ===')
    for c in cats:
        if c['model'] in ['Montero Sport', 'Avanza G', 'Vios', 'Innova', 'Mirage G4']:
            print(f"{c['brand']} {c['model']}: available_units={c['available_units']}, total_units={c['total_units']}")

    # 2. Test Units for Montero Sport (id 12 was Unavailable)
    res_m = client.get('/api/vehicles/units?brand=Mitsubishi&model=Montero%20Sport')
    print('=== UNITS: Mitsubishi Montero Sport ===')
    units_m = res_m.get_json()
    print(f'Count: {len(units_m)}')

    # 3. Test Units for Avanza G (id 24 was Unavailable)
    res_a = client.get('/api/vehicles/units?brand=Toyota&model=Avanza%20G')
    print('=== UNITS: Toyota Avanza G ===')
    units_a = res_a.get_json()
    print(f'Count: {len(units_a)}')

    # 4. Test Units for Toyota Vios (id 16 was Unavailable)
    res_v = client.get('/api/vehicles/units?brand=Toyota&model=Vios')
    print('=== UNITS: Toyota Vios ===')
    units_v = res_v.get_json()
    plates_v = [u['plate_number'] for u in units_v]
    print(f'Count: {len(units_v)}, Plates: {plates_v}')
    print(f'Is DBA 6730 (Unavailable) in results?: {"DBA 6730" in plates_v}')

    # 5. Test Availability Check on Vehicle 12 (Unavailable)
    res_avail_12 = client.post('/api/vehicles/check-availability', json={
        'vehicle_id': 12,
        'start_date': '2026-11-01',
        'end_date': '2026-11-03'
    })
    print('=== AVAILABILITY CHECK: Vehicle 12 (DUY 6527 - Unavailable) ===')
    print('Status code:', res_avail_12.status_code)
    print('Response:', res_avail_12.get_json())

    # 6. Test Availability Check on Vehicle 24 (Unavailable)
    res_avail_24 = client.post('/api/vehicles/check-availability', json={
        'vehicle_id': 24,
        'start_date': '2026-11-01',
        'end_date': '2026-11-03'
    })
    print('=== AVAILABILITY CHECK: Vehicle 24 (DAO 4897 - Unavailable) ===')
    print('Status code:', res_avail_24.status_code)
    print('Response:', res_avail_24.get_json())
