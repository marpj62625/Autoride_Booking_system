
import psycopg2
from psycopg2.extras import RealDictCursor

SUPABASE_DB_URL = 'postgresql://postgres.fydfsgjrlowrrtlmefwq:Autoride777%25*@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres'

def inspect_huy7652():
    try:
        conn = psycopg2.connect(SUPABASE_DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Check vehicle status
        cur.execute("SELECT id, brand, model, plate_number, status FROM vehicles WHERE plate_number = 'HUY 7652'")
        vehicle = cur.fetchone()
        if not vehicle:
            print("Vehicle HUY 7652 not found!")
            return
            
        print(f"VEHICLE: {vehicle['brand']} {vehicle['model']} | Plate: {vehicle['plate_number']} | Current DB Status: {vehicle['status']}")
        
        # 2. Check ANY non-cancelled bookings for this vehicle
        cur.execute("""
            SELECT id, user_id, start_date, end_date, status 
            FROM bookings 
            WHERE vehicle_id = %s 
            ORDER BY id DESC
        """, (vehicle['id'],))
        bookings = cur.fetchall()
        
        print("\n--- BOOKINGS FOR THIS VEHICLE ---")
        if not bookings:
            print("No bookings found.")
        else:
            for b in bookings:
                print(f"ID: {b['id']} | Status: {b['status']:12} | Period: {b['start_date']} to {b['end_date']}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    inspect_huy7652()
