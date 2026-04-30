import psycopg
from config import SUPABASE_DB_URL

def create_tables_and_data():
    conn = None
    try:
        # Connect to PostgreSQL (Supabase)
        conn = psycopg.connect(SUPABASE_DB_URL)
        cursor = conn.cursor()

        # In PostgreSQL with Supabase, you connect directly to the target database.
        # We do not need CREATE DATABASE or USE statements here.

        # Create Admins table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins(
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE,
                email VARCHAR(100) UNIQUE,
                password VARCHAR(255),
                role VARCHAR(20) DEFAULT 'SuperAdmin',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Table 'admins' created or verified successfully.")

        # Create Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id SERIAL PRIMARY KEY,
                full_name VARCHAR(100),
                email VARCHAR(100) UNIQUE,
                phone VARCHAR(20),
                password VARCHAR(255),
                license_image VARCHAR(255),
                profile_picture VARCHAR(255),
                is_verified BOOLEAN DEFAULT FALSE,
                google_id VARCHAR(255),
                auth_provider VARCHAR(50),
                loyalty_points INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Table 'users' created or verified successfully.")

        # Create Vehicles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles(
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                plate_number VARCHAR(20),
                brand VARCHAR(50),
                model VARCHAR(50),
                vehicle_type VARCHAR(20),
                transmission VARCHAR(20),
                fuel_type VARCHAR(20),
                seats INT,
                daily_rate DECIMAL(10,2),
                location VARCHAR(100),
                status VARCHAR(20),
                vehicle_image VARCHAR(255)
            )
        """)
        print("Table 'vehicles' created or verified successfully.")

        # Create Drivers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drivers(
                id SERIAL PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                license_number VARCHAR(50) NOT NULL UNIQUE,
                contact_info VARCHAR(120) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Table 'drivers' created or verified successfully.")

        # Create Coupons Table
        cursor.execute("""
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
        print("Table 'coupons' created or verified successfully.")

        # Create Bookings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings(
                id SERIAL PRIMARY KEY,
                user_id INT,
                vehicle_id INT,
                driver_id INT,
                start_date DATE,
                end_date DATE,
                pickup_location VARCHAR(100),
                rental_type VARCHAR(20),
                addons TEXT,
                insurance_type VARCHAR(50) DEFAULT 'Basic',
                insurance_price DECIMAL(10,2) DEFAULT 0,
                split_with_user_id INT DEFAULT NULL,
                split_status VARCHAR(50),
                split_with_email VARCHAR(100),
                base_price DECIMAL(10,2),
                addon_price DECIMAL(10,2),
                tax_amount DECIMAL(10,2),
                service_fee DECIMAL(10,2),
                total_price DECIMAL(10,2),
                applied_coupon_id INT REFERENCES coupons(id),
                discount_amount DECIMAL(10,2) DEFAULT 0,
                points_earned INT DEFAULT 0,
                points_redeemed INT DEFAULT 0,
                status VARCHAR(20)
            )
        """)
        print("Table 'bookings' created or verified successfully.")

        # Create Payments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments(
                id SERIAL PRIMARY KEY,
                booking_id INT,
                amount DECIMAL(10,2),
                method VARCHAR(50),
                reference_number VARCHAR(100),
                payment_proof VARCHAR(255),
                status VARCHAR(20)
            )
        """)
        print("Table 'payments' created or verified successfully.")

        # Create Reviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews(
                id SERIAL PRIMARY KEY,
                user_id INT,
                vehicle_id INT,
                rating INT,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Table 'reviews' created or verified successfully.")

        # Create Favorites table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites(
                user_id INT,
                vehicle_id INT,
                PRIMARY KEY (user_id, vehicle_id)
            )
        """)
        print("Table 'favorites' created or verified successfully.")

        # Create Saved Payments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_payments(
                id SERIAL PRIMARY KEY,
                user_id INT,
                card_type VARCHAR(20),
                last_four VARCHAR(4),
                provider VARCHAR(50)
            )
        """)
        print("Table 'saved_payments' created or verified successfully.")

        # Create Split Payments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS split_payments(
                id SERIAL PRIMARY KEY,
                booking_id INT,
                partner_email VARCHAR(100),
                amount DECIMAL(10,2),
                status VARCHAR(50)
            )
        """)
        print("Table 'split_payments' created or verified successfully.")

        # Insert mock vehicles
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("""
                INSERT INTO vehicles (plate_number, brand, model, vehicle_type, transmission, fuel_type, seats, daily_rate, location, status, vehicle_image)
                VALUES
                ('ABC123', 'Toyota', 'Vios', 'Sedan', 'Automatic', 'Gasoline', 5, 2500, 'Manila', 'Available', 'images/vios.png'),
                ('XYZ222', 'Toyota', 'Innova', 'SUV', 'Manual', 'Diesel', 7, 3500, 'Quezon City', 'Available', 'images/innova.png')
            """)
            conn.commit()
            print("Mock vehicle data inserted successfully.")
        else:
            print("Vehicle data already exists. Skipping insertion.")

        # New Enterprise Features Added

        # Add columns to users
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_frozen BOOLEAN DEFAULT FALSE")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS freeze_reason TEXT")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS province VARCHAR(100)")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS municipality VARCHAR(100)")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS barangay VARCHAR(100)")

        # Add columns to vehicles
        cursor.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS quantity INT DEFAULT 1")

        # Add columns to bookings
        cursor.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS pickup_province VARCHAR(100)")
        cursor.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS pickup_municipality VARCHAR(100)")
        cursor.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS pickup_barangay VARCHAR(100)")
        cursor.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS return_province VARCHAR(100)")
        cursor.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS return_municipality VARCHAR(100)")
        cursor.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS return_barangay VARCHAR(100)")

        # Create vehicle_images
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_images(
                id SERIAL PRIMARY KEY,
                vehicle_id INT NOT NULL,
                image_path VARCHAR(255) NOT NULL,
                is_primary BOOLEAN DEFAULT FALSE,
                order_index INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create pickup_instructions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pickup_instructions(
                id SERIAL PRIMARY KEY,
                icon VARCHAR(100) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL
            )
        """)

        # Create contact_queries
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

        # Create settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings(
                id SERIAL PRIMARY KEY,
                key VARCHAR(100) UNIQUE NOT NULL,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Table 'settings' created or verified successfully.")

        # Insert default settings if not exists
        default_settings = [
            ('service_fee_percent', '3', 'Service fee percentage per booking'),
            ('mileage_limit', '250', 'Daily mileage limit in kilometers'),
            ('long_term_discount_days', '7', 'Minimum days for long-term discount'),
            ('long_term_discount_percent', '10', 'Long-term discount percentage'),
            ('service_fee_fixed', '150', 'Fixed service fee per booking in PHP'),
            ('currency', 'PHP', 'System currency symbol'),
            ('time_zone', 'Asia/Manila', 'System time zone for date calculations'),
            ('rental_terms', 'Mileage Rule: 250 km per day. Rentals of 7 days or more get a 10% discount!', 'Global rental terms and conditions')
        ]
        
        for key, val, desc in default_settings:
            cursor.execute("INSERT INTO settings (key, value, description) VALUES (%s, %s, %s) ON CONFLICT (key) DO NOTHING", (key, val, desc))

        # Create activity_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs(
                id SERIAL PRIMARY KEY,
                admin_id INT,
                admin_name VARCHAR(255),
                action VARCHAR(100) NOT NULL,
                target_type VARCHAR(100),
                target_id VARCHAR(100),
                details TEXT,
                ip_address VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Table 'activity_logs' created or verified successfully.")

        conn.commit()
        print("Database setup completed successfully.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    print("Setting up Supabase PostgreSQL database...")
    create_tables_and_data()
    print("Database setup complete.")
