import psycopg
from config import SUPABASE_DB_URL
from psycopg.rows import dict_row

def check_phone():
    try:
        conn = psycopg.connect(SUPABASE_DB_URL)
        cursor = conn.cursor(row_factory=dict_row)
        
        cursor.execute("SELECT id, full_name, phone FROM users")
        users = cursor.fetchall()
        
        print(f"Total users found: {len(users)}")
        for u in users:
            print(f"ID: {u['id']} | Name: {u['full_name']} | Phone: {u['phone']}")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_phone()
