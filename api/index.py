import sys
import os

# Add the backend directory to the path so we can import app.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app

# Simpler handler for Vercel without stripping prefixes
# app.py already defines routes with /api/ prefix
handler = app
