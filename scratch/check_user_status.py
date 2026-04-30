from app import app
from database import get_cursor

with app.app_context():
    cur = get_cursor()
    cur.execute("SELECT id, full_name, email, is_email_verified, is_verified, auth_provider, password FROM users WHERE email='patrickciar78@gmail.com'")
    user = cur.fetchone()
    if user:
        # Convert to dict for printing
        user_dict = {
            'id': user[0],
            'full_name': user[1],
            'email': user[2],
            'is_email_verified': user[3],
            'is_verified': user[4],
            'auth_provider': user[5],
            'has_password': bool(user[6])
        }
        print(user_dict)
    else:
        print("Not found")
    cur.close()
