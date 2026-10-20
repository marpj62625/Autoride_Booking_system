import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
from app import app, get_cursor, commit_db

with app.app_context():
    cur = get_cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS email_verification_otps (
            email VARCHAR(255) PRIMARY KEY,
            otp VARCHAR(10) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)
    commit_db()
    print("Table email_verification_otps created successfully!")

    # Seed the current OTP for rnaa10061@gmail.com so user's current screen can verify immediately if tested
    cur.execute("""
        INSERT INTO email_verification_otps (email, otp, created_at)
        VALUES ('rnaa10061@gmail.com', '353963', NOW())
        ON CONFLICT (email) DO UPDATE SET otp = '353963', created_at = NOW();
    """)
    commit_db()
    print("Seeded 353963 for rnaa10061@gmail.com!")

    cur.execute("SELECT * FROM email_verification_otps")
    print("email_verification_otps rows:", cur.fetchall())
