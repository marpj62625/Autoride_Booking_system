import psycopg2
import os

# Connect string (from app.py)
conn_str = "postgresql://postgres.npxcftmtyigpxcizswce:M8uU3aJkK9vP5wQ@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

def check_drivers():
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT u.email, u.full_name, d.status FROM drivers d JOIN users u ON d.user_id = u.id WHERE d.status='Approved'")
    drivers = cur.fetchall()
    
    print("--- APPROVED DRIVERS ---")
    for d in drivers:
        print(f"Email: {d[0]}, Name: {d[1]}, Status: {d[2]}")
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_drivers()
