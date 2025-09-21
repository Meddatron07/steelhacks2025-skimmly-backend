#!/usr/bin/env python3
"""
Main application entry point for Render deployment
This file imports and runs the Flask app from the backend directory
"""

import sys
import os

# Add backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Change working directory to backend for relative imports
os.chdir(backend_path)

# Import and run the main Flask application
from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)