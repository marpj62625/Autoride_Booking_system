from app import app
from database import get_cursor, commit_db
import os

def fix_user():
    with app.app_context():
        try:
            cur = get_cursor()
            email = 'patrickciar78@gmail.com'
            # Set password to password123 and verify account
            cur.execute("UPDATE users SET password='password123', is_verified=1, is_email_verified=True WHERE email=%s", (email,))
            commit_db()
            print(f"Successfully updated {email}")
            cur.close()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    fix_user()
