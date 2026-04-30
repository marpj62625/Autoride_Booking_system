import psycopg
from config import SUPABASE_DB_URL

def update_db():
    conn = None
    try:
        conn = psycopg.connect(SUPABASE_DB_URL)
        cursor = conn.cursor()

        # Existing Updates
        # Add columns to drivers
        cursor.execute("ALTER TABLE drivers ADD COLUMN IF NOT EXISTS user_id INT UNIQUE")
        cursor.execute("ALTER TABLE drivers ADD COLUMN IF NOT EXISTS rejection_reason TEXT")
        print("Drivers table updated.")

        # Create settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings(
                key VARCHAR(50) PRIMARY KEY,
                value VARCHAR(255)
            )
        """)
        
        # Insert default wage
        cursor.execute("""
            INSERT INTO system_settings (key, value) VALUES ('driver_wage', '500') 
            ON CONFLICT (key) DO NOTHING
        """)
        print("System settings table created and populated.")
        
        # --- NEW UPDATES FOR ENTERPRISE FEATURES ---

        # 1. Users table update (Account Banning & Granular Address)
        print("Updating users table for freezing and addresses...")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_frozen BOOLEAN DEFAULT FALSE")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS freeze_reason TEXT")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS province VARCHAR(100)")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS municipality VARCHAR(100)")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS barangay VARCHAR(100)")

        # 2. Vehicles table update (Fleet Quantity)
        print("Updating vehicles table for quantity multiplier...")
        cursor.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS quantity INT DEFAULT 1")

        # 3. Bookings table update (Granular Pickup/Return)
        print("Updating bookings table for granular locations...")
        # We rename pickup_location conceptually or just add the granular ones.
        # Let's add the granular ones for pickup and return.
        cursor.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS pickup_province VARCHAR(100)")
        cursor.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS pickup_municipality VARCHAR(100)")
        cursor.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS pickup_barangay VARCHAR(100)")
        cursor.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS return_province VARCHAR(100)")
        cursor.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS return_municipality VARCHAR(100)")
        cursor.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS return_barangay VARCHAR(100)")

        # 4. Create Vehicle Images table
        print("Creating vehicle_images table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_images(
                id SERIAL PRIMARY KEY,
                vehicle_id INT NOT NULL,
                image_path VARCHAR(255) NOT NULL,
                is_primary BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. Create Pickup Instructions table
        print("Creating pickup_instructions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pickup_instructions(
                id SERIAL PRIMARY KEY,
                icon VARCHAR(100) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL
            )
        """)

        # 6. Create Contact Queries (Support Tickets) table
        print("Creating contact_queries table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_queries(
                id SERIAL PRIMARY KEY,
                user_id INT,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                subject VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                admin_reply TEXT,
                is_read BOOLEAN DEFAULT FALSE,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 7. Create Subscribers table for Newsletters
        print("Creating subscribers table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscribers(
                id SERIAL PRIMARY KEY,
                user_id INT,
                email VARCHAR(255) UNIQUE NOT NULL,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 8. Final touches to Users table (Auth separation & Granular Verification)
        print("Finishing Auth separation and granular verification updates...")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN DEFAULT FALSE")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_driver INT DEFAULT 0")
        
        # Migrate is_verified from BOOLEAN to INTEGER if needed
        cursor.execute("""
            SELECT data_type FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'is_verified'
        """)
        col_type = cursor.fetchone()[0]
        if col_type == 'boolean':
            print("Migrating is_verified from BOOLEAN to INTEGER...")
            cursor.execute("ALTER TABLE users ALTER COLUMN is_verified DROP DEFAULT")
            cursor.execute("ALTER TABLE users ALTER COLUMN is_verified TYPE INTEGER USING (CASE WHEN is_verified THEN 1 ELSE 0 END)")
            cursor.execute("ALTER TABLE users ALTER COLUMN is_verified SET DEFAULT 0")
            print("is_verified migrated successfully.")
        
        # Retroactively verify email for users who were already verified (likely via license/old system)
        cursor.execute("UPDATE users SET is_email_verified = TRUE WHERE is_verified = 1")
        
        conn.commit()
        print("All enterprise database updates completed successfully.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    update_db()
