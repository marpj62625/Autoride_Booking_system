import sys
import os

# Add the backend directory to the path so we can import app.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app

# Debug wrapper for Vercel
def debug_handler(environ, start_response):
    print(f"DEBUG: PATH_INFO = '{environ.get('PATH_INFO')}'")
    print(f"DEBUG: SCRIPT_NAME = '{environ.get('SCRIPT_NAME')}'")
    return app(environ, start_response)

handler = debug_handler
