
import psycopg2
from psycopg2.extras import RealDictCursor

SUPABASE_DB_URL = 'postgresql://postgres.fydfsgjrlowrrtlmefwq:Autoride777%25*@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres'

def debug_cancellation():
    try:
        conn = psycopg2.connect(SUPABASE_DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check the last 10 bookings and their vehicles
        cur.execute("""
            SELECT b.id as booking_id, b.status as booking_status, v.id as vehicle_id, v.status as vehicle_status, v.brand, v.model
            FROM bookings b
            JOIN vehicles v ON b.vehicle_id = v.id
            ORDER BY b.id DESC
            LIMIT 10
        """)
        rows = cur.fetchall()
        print(f"{'ID':<4} | {'Booking Status':<15} | {'Veh Status':<12} | {'Vehicle':<20}")
        print("-" * 60)
        for r in rows:
            print(f"{r['booking_id']:<4} | {r['booking_status']:<15} | {r['vehicle_status']:<12} | {r['brand']} {r['model']}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    debug_cancellation()
