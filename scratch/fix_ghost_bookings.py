
import psycopg2
from psycopg2.extras import RealDictCursor

SUPABASE_DB_URL = 'postgresql://postgres.fydfsgjrlowrrtlmefwq:Autoride777%25*@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres'

def fix_ghost_bookings():
    try:
        conn = psycopg2.connect(SUPABASE_DB_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Find all vehicles that are 'Booked'
        cur.execute("SELECT id, brand, model, plate_number FROM vehicles WHERE status = 'Booked'")
        booked_vehicles = cur.fetchall()
        
        print(f"Found {len(booked_vehicles)} vehicles marked as 'Booked'.")
        
        for v in booked_vehicles:
            # Check if there are any Confirmed, Pending, or Picked Up bookings for this vehicle
            cur.execute("""
                SELECT id, status FROM bookings 
                WHERE vehicle_id = %s 
                AND status IN ('Confirmed', 'Pending', 'Picked Up', 'Ongoing')
            """, (v['id'],))
            active_bookings = cur.fetchall()
            
            if not active_bookings:
                print(f"FIXING: Vehicle {v['id']} ({v['brand']} {v['model']}) has NO active bookings but is marked as 'Booked'. Resetting to 'Available'.")
                cur.execute("UPDATE vehicles SET status = 'Available' WHERE id = %s", (v['id'],))
            else:
                print(f"KEEPING: Vehicle {v['id']} ({v['brand']} {v['model']}) has {len(active_bookings)} active bookings.")
        
        conn.commit()
        print("Done!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    fix_ghost_bookings()
