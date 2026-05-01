import sys
import os

# Add the backend directory to the path so we can import app.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app

# This is required for Vercel
# We expose the flask app as 'app'
# Vercel's python builder will look for this
# For Vercel, we might need to handle the /api prefix
class PrefixMiddleware(object):
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'].startswith(self.prefix):
            # This is already handled by Vercel's rewrite, but let's be sure
            return self.app(environ, start_response)
        return self.app(environ, start_response)

# handler = PrefixMiddleware(app, prefix='/api')
handler = app
