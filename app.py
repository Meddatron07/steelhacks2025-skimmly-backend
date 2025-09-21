#!/usr/bin/env python3
"""
Main application entry point for Render deployment
Creates the 'app' variable that gunicorn expects to find
"""

import sys
import os

# Add backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Change working directory to backend for relative imports and file access
original_cwd = os.getcwd()
os.chdir(backend_path)

try:
    # Import the Flask application from backend
    from app import app
except ImportError as e:
    # If import fails, change back to original directory and re-raise
    os.chdir(original_cwd)
    raise e

# This is the variable that gunicorn will look for
app = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)