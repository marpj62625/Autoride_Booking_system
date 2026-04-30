
import psycopg2

SUPABASE_DB_URL = 'postgresql://postgres.fydfsgjrlowrrtlmefwq:Autoride777%25*@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres'

def force_available():
    try:
        conn = psycopg2.connect(SUPABASE_DB_URL)
        cur = conn.cursor()
        
        # Force HUY 7652 to Available
        cur.execute("UPDATE vehicles SET status = 'Available' WHERE plate_number = 'HUY 7652'")
        print(f"Rows affected: {cur.rowcount}")
        
        # Also check if there are any Confirmed/Pending bookings for it and mark them as Cancelled
        cur.execute("UPDATE bookings SET status = 'Cancelled' WHERE vehicle_id = (SELECT id FROM vehicles WHERE plate_number = 'HUY 7652') AND status IN ('Pending', 'Confirmed')")
        print(f"Bookings cancelled: {cur.rowcount}")
        
        conn.commit()
        print("Force reset successful!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    force_available()
