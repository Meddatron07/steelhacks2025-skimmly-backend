#!/usr/bin/env python3
"""
Script to recreate the database with all new columns
"""
import os
from app import app, db

def recreate_database():
    """Recreate the database with all tables"""
    # Remove existing database
    db_path = 'notes_app.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")

    # Create all tables with current schema
    with app.app_context():
        db.create_all()
        print("Database recreated successfully!")
        print("Tables created:")

        # Show tables
        result = db.engine.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for row in result:
            print(f"  - {row[0]}")

if __name__ == '__main__':
    recreate_database()