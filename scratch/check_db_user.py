import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
from app import app, get_cursor, commit_db

with app.app_context():
    cur = get_cursor()
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' ORDER BY ordinal_position")
    rows = cur.fetchall()
    print("Users columns:")
    for r in rows:
        print(f"  {r['column_name']} ({r['data_type']})")

    cur.execute("SELECT id, email, is_email_verified, is_verified FROM users WHERE email = 'rnaa10061@gmail.com'")
    user = cur.fetchone()
    print("\nUser rnaa10061@gmail.com:", user)
