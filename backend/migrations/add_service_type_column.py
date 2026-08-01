import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database import get_connection, release_connection

def run_migration():
    conn = get_connection()
    cur = conn.cursor()
    
    # Check if service_type column exists
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='bookings' AND column_name='service_type'
    """)
    if not cur.fetchone():
        print("Adding service_type column to bookings table...")
        cur.execute("ALTER TABLE bookings ADD COLUMN service_type VARCHAR(50) DEFAULT 'pickup'")
        conn.commit()
        print("Column service_type added successfully.")
    else:
        print("Column service_type already exists.")
        
    cur.close()
    release_connection(conn)

if __name__ == '__main__':
    run_migration()
