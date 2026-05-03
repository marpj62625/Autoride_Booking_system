import sys
import os

# Add the backend directory to the path so we can import app.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app

# This middleware strips the /api prefix AND optional trailing slash before passing it to Flask
class PrefixMiddleware(object):
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        
        # 1. Strip the /api prefix
        if path.startswith(self.prefix):
            path = path[len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
        
        # 2. Strip trailing slash to ensure matching with Flask routes (e.g. /admin/stats/ -> /admin/stats)
        if len(path) > 1 and path.endswith('/'):
            path = path[:-1]
            
        environ['PATH_INFO'] = path
        return self.app(environ, start_response)

# Middleware removed because /api prefix is now handled directly in app.py routes
# app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix='/api')

# Handler for Vercel
handler = app
