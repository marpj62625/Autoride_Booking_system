import psycopg
import os
import sys

# Add backend to path for config import
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from config import SUPABASE_DB_URL

def update_settings():
    try:
        conn = psycopg.connect(SUPABASE_DB_URL)
        cur = conn.cursor()
        
        # 1. Remove tax_rate
        cur.execute("DELETE FROM settings WHERE key = 'tax_rate'")
        
        # 2. Add new settings
        new_settings = [
            ('service_fee_percent', '3', 'Service fee percentage per booking'),
            ('mileage_limit', '250', 'Daily mileage limit in kilometers'),
            ('long_term_discount_days', '7', 'Minimum days for long-term discount'),
            ('long_term_discount_percent', '10', 'Long-term discount percentage'),
        ]
        
        for key, val, desc in new_settings:
            cur.execute("""
                INSERT INTO settings (key, value, description) 
                VALUES (%s, %s, %s) 
                ON CONFLICT (key) DO UPDATE SET description = EXCLUDED.description
            """, (key, val, desc))
            
        # 3. Update rental terms
        terms = "Mileage Rule: 250 km per day. Rentals of 7 days or more get a 10% discount!"
        cur.execute("UPDATE settings SET value = %s WHERE key = 'rental_terms'", (terms,))
        
        conn.commit()
        print("Database settings updated successfully.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_settings()
