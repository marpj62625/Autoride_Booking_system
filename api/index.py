
import sys
import os

# Add the backend directory to the path so we can import app.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app

# This is required for Vercel
# We expose the flask app as 'app'
# Vercel's python builder will look for this
handler = app
