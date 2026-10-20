import sys
import os
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from app import app, get_cursor, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

with app.app_context():
    cur = get_cursor()
    cur.execute("SELECT key, value FROM settings WHERE key LIKE 'smtp_oauth%'")
    s = {r['key']: r['value'] for r in cur.fetchall()}
    print("Stored email:", s.get('smtp_oauth_email'))
    print("Refresh token exists:", bool(s.get('smtp_oauth_refresh_token')))
    print("Client ID:", GOOGLE_CLIENT_ID)
    print("Client Secret exists:", bool(GOOGLE_CLIENT_SECRET))
    
    data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'refresh_token': s.get('smtp_oauth_refresh_token'),
        'grant_type': 'refresh_token'
    }
    res = requests.post('https://oauth2.googleapis.com/token', data=data)
    print("OAuth response status:", res.status_code)
    print("OAuth response body:", res.text)
    cur.close()
