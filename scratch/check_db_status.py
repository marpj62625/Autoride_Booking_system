
import psycopg2
from psycopg2.extras import RealDictCursor
import os

def check_status():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/postgres")
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("--- RECENT BOOKINGS ---")
    cur.execute("SELECT id, vehicle_id, status FROM bookings ORDER BY id DESC LIMIT 5")
    bookings = cur.fetchall()
    for b in bookings:
        print(f"Booking #{b['id']}: Status={b['status']}, VehicleID={b['vehicle_id']}")
        
    print("\n--- VEHICLE STATUSES ---")
    if bookings:
        v_ids = tuple(b['vehicle_id'] for b in bookings)
        cur.execute("SELECT id, brand, model, status FROM vehicles WHERE id IN %s", (v_ids,))
        vehicles = cur.fetchall()
        for v in vehicles:
            print(f"Vehicle #{v['id']} ({v['brand']} {v['model']}): Status={v['status']}")
            
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_status()
