import sys
import os

# Add backend to path to import database config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import psycopg
from config import SUPABASE_DB_URL

def update_database():
    try:
        print("Connecting to Supabase PostgreSQL...")
        with psycopg.connect(SUPABASE_DB_URL) as conn:
            with conn.cursor() as cur:
                # 1. Update Users Table for Loyalty Points
                print("Updating 'users' table...")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS loyalty_points INT DEFAULT 0")

                # 2. Create Coupons Table
                print("Creating 'coupons' table...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS coupons (
                        id SERIAL PRIMARY KEY,
                        code VARCHAR(50) UNIQUE NOT NULL,
                        discount_percent INTEGER NOT NULL CHECK (discount_percent > 0 AND discount_percent <= 100),
                        expiry_date DATE NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        usage_limit INTEGER DEFAULT NULL,
                        times_used INTEGER DEFAULT 0,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Seed test coupons
                cur.execute("INSERT INTO coupons (code, discount_percent, expiry_date, is_active) VALUES ('AUTORIDE10', 10, '2027-12-31', TRUE) ON CONFLICT DO NOTHING")
                cur.execute("INSERT INTO coupons (code, discount_percent, expiry_date, is_active) VALUES ('WELCOME20', 20, '2027-12-31', TRUE) ON CONFLICT DO NOTHING")

                # 3. Update Bookings Table for Financial Tracking
                print("Updating 'bookings' table...")
                cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS applied_coupon_id INT REFERENCES coupons(id)")
                cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS discount_amount DECIMAL(10,2) DEFAULT 0")
                cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS points_earned INT DEFAULT 0")
                cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS points_redeemed INT DEFAULT 0")

                conn.commit()
                print("\nDatabase updated successfully with Enterprise features!")

    except Exception as e:
        print(f"Error updating database: {e}")

if __name__ == "__main__":
    update_database()
