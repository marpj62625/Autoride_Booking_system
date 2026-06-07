"""
Migration script to remove driver-related tables and columns from the database.
This script:
1. Drops the drivers table
2. Removes driver_id column from bookings table
3. Removes driver-related foreign key constraints
"""

import psycopg
from config import SUPABASE_DB_URL

def migrate_remove_drivers():
    """Remove all driver-related database components."""
    conn = None
    try:
        conn = psycopg.connect(SUPABASE_DB_URL)
        cursor = conn.cursor()

        print("Starting driver removal migration...")

        # 1. Drop foreign key constraint from bookings to drivers (if exists)
        print("Dropping foreign key constraint fk_bookings_driver...")
        cursor.execute("""
            ALTER TABLE bookings 
            DROP CONSTRAINT IF EXISTS fk_bookings_driver
        """)

        # 2. Drop driver_id column from bookings table
        print("Dropping driver_id column from bookings...")
        cursor.execute("""
            ALTER TABLE bookings 
            DROP COLUMN IF EXISTS driver_id
        """)

        # 3. Drop drivers table
        print("Dropping drivers table...")
        cursor.execute("""
            DROP TABLE IF EXISTS drivers CASCADE
        """)

        conn.commit()
        print("? Driver removal migration completed successfully!")
        print("  - Dropped drivers table")
        print("  - Removed driver_id column from bookings")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"? Migration failed: {e}")
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("DRIVER REMOVAL MIGRATION")
    print("=" * 60)
    migrate_remove_drivers()
    print("=" * 60)
