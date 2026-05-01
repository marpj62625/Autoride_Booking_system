
import sys
import os

# Add the backend directory to the path so we can import app.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from app import app
    handler = app
except Exception as e:
    import traceback
    def handler(environ, start_response):
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        error_msg = f"CRASH DURING STARTUP:\n{str(e)}\n\n{traceback.format_exc()}"
        return [error_msg.encode()]
