import os
import psycopg
from database import get_connection, release_connection

def run_migration():
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # 1. Ensure booking_extensions table exists and has all columns
        cur.execute("""
            CREATE TABLE IF NOT EXISTS booking_extensions (
                id                BIGSERIAL PRIMARY KEY,
                booking_id        INTEGER NOT NULL,
                requested_by      INTEGER NOT NULL,
                original_end_date DATE NOT NULL,
                new_end_date      DATE NOT NULL,
                extension_days    INTEGER NOT NULL,
                extension_price   NUMERIC(12,2) NOT NULL,
                payment_method    VARCHAR(100),
                reference_number  VARCHAR(200),
                payment_proof_url TEXT,
                status            VARCHAR(20) DEFAULT 'pending',
                admin_note        TEXT,
                created_at        TIMESTAMPTZ DEFAULT NOW(),
                updated_at        TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Check and add columns for booking_extensions
        extensions_cols = {
            'approved_by_admin_id': 'INTEGER',
            'approved_at': 'TIMESTAMPTZ',
            'has_conflicts': 'BOOLEAN DEFAULT FALSE'
        }
        for col, col_type in extensions_cols.items():
            cur.execute(f"""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='booking_extensions' AND column_name='{col}'
            """)
            if not cur.fetchone():
                print(f"Adding column {col} to booking_extensions")
                cur.execute(f"ALTER TABLE booking_extensions ADD COLUMN {col} {col_type}")

        # 2. Add columns to bookings table
        bookings_cols = {
            'has_active_extension': 'BOOLEAN DEFAULT FALSE',
            'extension_count': 'INT DEFAULT 0',
            'is_conflict_affected': 'BOOLEAN DEFAULT FALSE',
            'conflict_id': 'INT DEFAULT NULL'
        }
        for col, col_type in bookings_cols.items():
            cur.execute(f"""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='bookings' AND column_name='{col}'
            """)
            if not cur.fetchone():
                print(f"Adding column {col} to bookings")
                cur.execute(f"ALTER TABLE bookings ADD COLUMN {col} {col_type}")

        # 3. Create booking_conflicts table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS booking_conflicts (
                id                              BIGSERIAL PRIMARY KEY,
                extension_id                    INTEGER NOT NULL,
                affected_booking_id             INTEGER NOT NULL,
                affected_user_id                INTEGER NOT NULL,
                conflict_start_date             DATE,
                conflict_end_date               DATE,
                resolution_status               VARCHAR(50) DEFAULT 'Pending',
                resolution_deadline             TIMESTAMPTZ,
                selected_alternative_vehicle_id INTEGER,
                refund_amount                   NUMERIC(12,2),
                refund_status                   VARCHAR(50) DEFAULT 'Pending',
                refund_transaction_id           VARCHAR(200),
                customer_notified_at            TIMESTAMPTZ,
                customer_responded_at           TIMESTAMPTZ,
                created_at                      TIMESTAMPTZ DEFAULT NOW(),
                updated_at                      TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        conn.commit()
        print("Database migration completed successfully.")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print("Migration failed:", e)
        raise e
    finally:
        if conn:
            release_connection(conn)

if __name__ == '__main__':
    run_migration()
