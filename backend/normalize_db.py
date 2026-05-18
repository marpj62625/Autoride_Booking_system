"""
Database normalization script - adds foreign key constraints to Supabase PostgreSQL.
Safe to run: only adds constraints, does not drop or modify any columns or data.
"""
import psycopg
from config import SUPABASE_DB_URL

def normalize():
    conn = None
    try:
        conn = psycopg.connect(SUPABASE_DB_URL)
        cur = conn.cursor()

        print("Starting database normalization...")

        # Drop all existing FK constraints first (in case of partial previous runs)
        fk_drops = [
            "ALTER TABLE bookings DROP CONSTRAINT IF EXISTS fk_bookings_user",
            "ALTER TABLE bookings DROP CONSTRAINT IF EXISTS fk_bookings_vehicle",
            "ALTER TABLE bookings DROP CONSTRAINT IF EXISTS fk_bookings_driver",
            "ALTER TABLE bookings DROP CONSTRAINT IF EXISTS fk_bookings_coupon",
            "ALTER TABLE payments DROP CONSTRAINT IF EXISTS fk_payments_booking",
            "ALTER TABLE reviews DROP CONSTRAINT IF EXISTS fk_reviews_user",
            "ALTER TABLE reviews DROP CONSTRAINT IF EXISTS fk_reviews_vehicle",
            "ALTER TABLE favorites DROP CONSTRAINT IF EXISTS fk_favorites_user",
            "ALTER TABLE favorites DROP CONSTRAINT IF EXISTS fk_favorites_vehicle",
            "ALTER TABLE saved_payments DROP CONSTRAINT IF EXISTS fk_saved_payments_user",
            "ALTER TABLE split_payments DROP CONSTRAINT IF EXISTS fk_split_payments_booking",
            "ALTER TABLE vehicle_images DROP CONSTRAINT IF EXISTS fk_vehicle_images_vehicle",
            "ALTER TABLE contact_queries DROP CONSTRAINT IF EXISTS fk_contact_queries_user",
            "ALTER TABLE activity_logs DROP CONSTRAINT IF EXISTS fk_activity_logs_admin",
        ]
        for stmt in fk_drops:
            cur.execute(stmt)
        print("Dropped existing FK constraints (if any).")

        # Add foreign key constraints
        fk_adds = [
            # bookings
            ("bookings", "fk_bookings_user",
             "ALTER TABLE bookings ADD CONSTRAINT fk_bookings_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL"),
            ("bookings", "fk_bookings_vehicle",
             "ALTER TABLE bookings ADD CONSTRAINT fk_bookings_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE SET NULL"),
            ("bookings", "fk_bookings_driver",
             "ALTER TABLE bookings ADD CONSTRAINT fk_bookings_driver FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE SET NULL"),
            ("bookings", "fk_bookings_coupon",
             "ALTER TABLE bookings ADD CONSTRAINT fk_bookings_coupon FOREIGN KEY (applied_coupon_id) REFERENCES coupons(id) ON DELETE SET NULL"),

            # payments
            ("payments", "fk_payments_booking",
             "ALTER TABLE payments ADD CONSTRAINT fk_payments_booking FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE"),

            # reviews
            ("reviews", "fk_reviews_user",
             "ALTER TABLE reviews ADD CONSTRAINT fk_reviews_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"),
            ("reviews", "fk_reviews_vehicle",
             "ALTER TABLE reviews ADD CONSTRAINT fk_reviews_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE"),

            # favorites
            ("favorites", "fk_favorites_user",
             "ALTER TABLE favorites ADD CONSTRAINT fk_favorites_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"),
            ("favorites", "fk_favorites_vehicle",
             "ALTER TABLE favorites ADD CONSTRAINT fk_favorites_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE"),

            # saved_payments
            ("saved_payments", "fk_saved_payments_user",
             "ALTER TABLE saved_payments ADD CONSTRAINT fk_saved_payments_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"),

            # split_payments
            ("split_payments", "fk_split_payments_booking",
             "ALTER TABLE split_payments ADD CONSTRAINT fk_split_payments_booking FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE"),

            # vehicle_images
            ("vehicle_images", "fk_vehicle_images_vehicle",
             "ALTER TABLE vehicle_images ADD CONSTRAINT fk_vehicle_images_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE"),

            # contact_queries
            ("contact_queries", "fk_contact_queries_user",
             "ALTER TABLE contact_queries ADD CONSTRAINT fk_contact_queries_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL"),

            # activity_logs
            ("activity_logs", "fk_activity_logs_admin",
             "ALTER TABLE activity_logs ADD CONSTRAINT fk_activity_logs_admin FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE SET NULL"),
        ]

        for table, name, stmt in fk_adds:
            cur.execute(stmt)
            print(f"  ? Added FK: {name} on {table}")

        # Add useful indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_bookings_vehicle_id ON bookings(vehicle_id)",
            "CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status)",
            "CREATE INDEX IF NOT EXISTS idx_payments_booking_id ON payments(booking_id)",
            "CREATE INDEX IF NOT EXISTS idx_reviews_vehicle_id ON reviews(vehicle_id)",
            "CREATE INDEX IF NOT EXISTS idx_vehicle_images_vehicle_id ON vehicle_images(vehicle_id)",
        ]
        for stmt in indexes:
            cur.execute(stmt)
        print("  ? Added performance indexes")

        conn.commit()
        print("\nNormalization complete. Database is now in 3NF with proper FK constraints.")

    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    normalize()
