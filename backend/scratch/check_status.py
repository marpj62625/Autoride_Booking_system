import psycopg
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row

def check_vehicles():
    try:
        conn = psycopg.connect(SUPABASE_DB_URL)
        cur = conn.cursor(row_factory=dict_row)
        cur.execute("SELECT id, name, status FROM vehicles")
        vehicles = cur.fetchall()
        print("\nVEHICLE STATUS CHECK:")
        print("-" * 40)
        for v in vehicles:
            print(f"ID: {v['id']} | Name: {v['name']} | Status: {v['status']}")
        print("-" * 40)
        
        cur.execute("SELECT id, vehicle_id, status FROM bookings ORDER BY id DESC LIMIT 5")
        bookings = cur.fetchall()
        print("\nRECENT BOOKINGS:")
        print("-" * 40)
        for b in bookings:
            print(f"ID: {b['id']} | Vehicle ID: {b['vehicle_id']} | Status: {b['status']}")
        print("-" * 40)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_vehicles()
