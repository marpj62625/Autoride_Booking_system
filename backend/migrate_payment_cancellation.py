import sys
import os

# Add backend directory to path so we can import from database.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_cursor, commit_db

def migrate():
    try:
        cur = get_cursor()
        
        # Add new columns for partial payments and cancellations
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS payment_type VARCHAR(50) DEFAULT 'Full'")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS amount_paid DECIMAL(10,2) DEFAULT 0")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS balance_amount DECIMAL(10,2) DEFAULT 0")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS cancellation_reason TEXT")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS cancelled_by VARCHAR(50)")
        
        commit_db()
        print("Successfully migrated bookings table for Payments and Cancellations!")
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        if 'cur' in locals():
            cur.close()

if __name__ == "__main__":
    migrate()
