"""
Migration: Add Booking Extension and Conflict Resolution Tables
Version: 001
Created: 2024
Description: 
    Creates tables for booking extension feature with conflict resolution:
    - booking_extensions: Stores extension requests and approvals
    - booking_conflicts: Tracks conflicts when extensions overlap with future bookings
    - extension_payments: Records payment transactions for approved extensions
    - Adds new columns to bookings table for extension tracking
"""

import psycopg
from config import SUPABASE_DB_URL


def migrate_up():
    """Apply the migration"""
    conn = None
    try:
        conn = psycopg.connect(SUPABASE_DB_URL)
        cursor = conn.cursor()
        
        print("Starting migration: Add extension tables...")
        
        # 1. Create booking_extensions table
        print("Creating booking_extensions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS booking_extensions (
                extension_id SERIAL PRIMARY KEY,
                booking_id INT NOT NULL,
                requested_by_user_id INT NOT NULL,
                original_end_date DATE NOT NULL,
                requested_end_date DATE NOT NULL,
                additional_days INT NOT NULL,
                additional_cost DECIMAL(10,2) NOT NULL,
                status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Rejected', 'Cancelled')),
                admin_notes TEXT,
                approved_by_admin_id INT,
                approved_at TIMESTAMP,
                has_conflicts BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
                FOREIGN KEY (requested_by_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (approved_by_admin_id) REFERENCES admins(id) ON DELETE SET NULL
            )
        """)
        print("? booking_extensions table created")
        
        # 2. Create booking_conflicts table
        print("Creating booking_conflicts table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS booking_conflicts (
                conflict_id SERIAL PRIMARY KEY,
                extension_id INT NOT NULL,
                affected_booking_id INT NOT NULL,
                affected_user_id INT NOT NULL,
                conflict_start_date DATE NOT NULL,
                conflict_end_date DATE NOT NULL,
                resolution_status VARCHAR(30) DEFAULT 'Pending' CHECK (resolution_status IN ('Pending', 'Alternative_Selected', 'Refund_Processed', 'Auto_Cancelled')),
                resolution_deadline TIMESTAMP NOT NULL,
                selected_alternative_vehicle_id INT,
                refund_amount DECIMAL(10,2),
                refund_status VARCHAR(20) CHECK (refund_status IN ('Pending', 'Processing', 'Completed', 'Failed')),
                refund_transaction_id VARCHAR(100),
                customer_notified_at TIMESTAMP,
                customer_responded_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (extension_id) REFERENCES booking_extensions(extension_id) ON DELETE CASCADE,
                FOREIGN KEY (affected_booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
                FOREIGN KEY (affected_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (selected_alternative_vehicle_id) REFERENCES vehicles(id) ON DELETE SET NULL
            )
        """)
        print("? booking_conflicts table created")
        
        # 3. Create extension_payments table
        print("Creating extension_payments table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extension_payments (
                payment_id SERIAL PRIMARY KEY,
                extension_id INT NOT NULL,
                booking_id INT NOT NULL,
                user_id INT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('GCash', 'Maya', 'PayMongo', 'Cash')),
                payment_status VARCHAR(20) DEFAULT 'Pending' CHECK (payment_status IN ('Pending', 'Completed', 'Failed', 'Refunded')),
                payment_proof_url VARCHAR(500),
                transaction_reference VARCHAR(100),
                paid_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (extension_id) REFERENCES booking_extensions(extension_id) ON DELETE CASCADE,
                FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        print("? extension_payments table created")
        
        # 4. Add new columns to bookings table (with DEFAULT values for backward compatibility)
        print("Adding extension tracking columns to bookings table...")
        cursor.execute("""
            ALTER TABLE bookings 
            ADD COLUMN IF NOT EXISTS has_active_extension BOOLEAN DEFAULT FALSE
        """)
        cursor.execute("""
            ALTER TABLE bookings 
            ADD COLUMN IF NOT EXISTS extension_count INT DEFAULT 0
        """)
        cursor.execute("""
            ALTER TABLE bookings 
            ADD COLUMN IF NOT EXISTS is_conflict_affected BOOLEAN DEFAULT FALSE
        """)
        cursor.execute("""
            ALTER TABLE bookings 
            ADD COLUMN IF NOT EXISTS conflict_id INT DEFAULT NULL
        """)
        print("? New columns added to bookings table")
        
        # 5. Add foreign key constraint for conflict_id (added separately after column creation)
        print("Adding foreign key constraint for bookings.conflict_id...")
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'bookings_conflict_id_fkey'
                ) THEN
                    ALTER TABLE bookings 
                    ADD CONSTRAINT bookings_conflict_id_fkey 
                    FOREIGN KEY (conflict_id) REFERENCES booking_conflicts(conflict_id) ON DELETE SET NULL;
                END IF;
            END $$;
        """)
        print("? Foreign key constraint added")
        
        # 6. Create indexes on frequently queried columns
        print("Creating indexes for performance optimization...")
        
        # Indexes for booking_extensions
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_booking_extensions_booking_id 
            ON booking_extensions(booking_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_booking_extensions_status 
            ON booking_extensions(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_booking_extensions_created_at 
            ON booking_extensions(created_at)
        """)
        
        # Indexes for booking_conflicts
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_booking_conflicts_affected_booking_id 
            ON booking_conflicts(affected_booking_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_booking_conflicts_resolution_status 
            ON booking_conflicts(resolution_status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_booking_conflicts_resolution_deadline 
            ON booking_conflicts(resolution_deadline)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_booking_conflicts_created_at 
            ON booking_conflicts(created_at)
        """)
        
        # Indexes for extension_payments
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_extension_payments_extension_id 
            ON extension_payments(extension_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_extension_payments_payment_status 
            ON extension_payments(payment_status)
        """)
        
        print("? Indexes created successfully")
        
        # Commit all changes
        conn.commit()
        print("\n? Migration completed successfully!")
        print("Tables created: booking_extensions, booking_conflicts, extension_payments")
        print("Bookings table updated with extension tracking columns")
        print("All indexes created for optimized queries")
        
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"\n? Migration failed: {e}")
        raise
        
    finally:
        if conn:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    print("=" * 70)
    print("Running Migration: 001_add_extension_tables")
    print("=" * 70)
    migrate_up()
