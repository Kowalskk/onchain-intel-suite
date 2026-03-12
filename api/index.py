import sys
import os

# Ensure the backend directory is in the path for relative imports in main.py
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app

# This entry point is for Vercel's Python runtime
# Vercel will look for 'app' usually, or we can use the default export
