#!/usr/bin/env python3
"""
Migration script to add Firebase UID column to existing database
"""
from app import app, db, User
import sqlite3

def migrate_database():
    """Add firebase_uid column to users table"""
    with app.app_context():
        try:
            # Use db.session.execute for SQLAlchemy 2.x compatibility
            from sqlalchemy import text
            db.session.execute(text('ALTER TABLE user ADD COLUMN firebase_uid VARCHAR(128)'))
            db.session.commit()
            print("firebase_uid column added successfully")
        except Exception as e:
            if 'duplicate column name' in str(e).lower():
                print("firebase_uid column already exists")
            else:
                print(f"Error adding column: {e}")
                return False

        try:
            # Make password_hash nullable for Firebase users
            # SQLite doesn't support ALTER COLUMN directly, so we'll handle this in app logic
            print("Database migration completed")
            return True
        except Exception as e:
            print(f"Error during migration: {e}")
            return False

if __name__ == '__main__':
    migrate_database()