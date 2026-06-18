import sys
import os

# Add the backend directory to the path so we can import app.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app  # v2026.05.12

# This middleware strips the /api prefix before passing to Flask
# Vercel receives /api/vehicles/categories -> middleware strips -> Flask sees /vehicles/categories
class PrefixMiddleware(object):
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')

        # Strip the /api prefix
        if path.startswith(self.prefix):
            path = path[len(self.prefix):]
            if not path.startswith('/'):
                path = '/' + path
            environ['SCRIPT_NAME'] = self.prefix

        # Strip trailing slash
        if len(path) > 1 and path.endswith('/'):
            path = path[:-1]

        environ['PATH_INFO'] = path
        return self.app(environ, start_response)

# Apply the middleware - strips /api so Flask routes don't need /api prefix
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix='/api')

# Handler for Vercel
handler = app
