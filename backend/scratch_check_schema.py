from app import app
from database import get_cursor

def check_schema():
    with app.app_context():
        try:
            cur = get_cursor()
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'bookings'")
            columns = cur.fetchall()
            print([c[0] for c in columns])
            cur.close()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
