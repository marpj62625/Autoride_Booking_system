import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def check_verification_statuses():
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT id, full_name, email, is_verified, is_email_verified, license_image FROM users ORDER BY id ASC")
    users = cur.fetchall()
    
    print(f"{'ID':<4} | {'Name':<20} | {'Email Verified':<14} | {'License Status':<14} | {'License Image'}")
    print("-" * 80)
    for u in users:
        lic_status = "Pending (0)" if u['is_verified'] == 0 else "Approved (1)" if u['is_verified'] == 1 else "Rejected (2)"
        lic_img = "Yes" if u['license_image'] else "No"
        print(f"{u['id']:<4} | {u['full_name'][:20]:<20} | {str(u['is_email_verified']):<14} | {lic_status:<14} | {lic_img}")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    check_verification_statuses()
