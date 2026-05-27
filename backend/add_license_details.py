import sys
import os
from database import get_connection

def create_table():
    conn = get_connection()
    try:
        cur = conn.cursor()
        print("Creating license_details table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS license_details (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) UNIQUE,
                full_name VARCHAR(255) NOT NULL,
                date_of_birth DATE NOT NULL,
                license_number VARCHAR(100) NOT NULL,
                expiry_date DATE NOT NULL,
                issuing_country_state VARCHAR(100) NOT NULL,
                license_class VARCHAR(50) NOT NULL,
                emergency_contact_name VARCHAR(255) NOT NULL,
                emergency_contact_phone VARCHAR(50) NOT NULL,
                emergency_contact_relationship VARCHAR(100) NOT NULL,
                license_front_url TEXT NOT NULL,
                license_back_url TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("Table created successfully.")
    except Exception as e:
        print("Error creating table:", e)
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_table()
