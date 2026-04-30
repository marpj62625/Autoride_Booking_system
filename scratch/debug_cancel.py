
import psycopg2
from psycopg2.extras import RealDictCursor

def debug_cancellation():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/postgres")
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check the last 5 bookings and their vehicles
    cur.execute("""
        SELECT b.id as booking_id, b.status as booking_status, v.id as vehicle_id, v.status as vehicle_status, v.brand, v.model
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        ORDER BY b.id DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    print("ID | Booking Status | Veh Status | Vehicle")
    print("-" * 50)
    for r in rows:
        print(f"{r['booking_id']} | {r['booking_status']:14} | {r['vehicle_status']:10} | {r['brand']} {r['model']}")
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    debug_cancellation()
