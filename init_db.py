#!/usr/bin/env python
"""
Database initialization script.
Run this to create all database tables.
"""

import sys
import os
from app import app, db
from models import User, Document, DocumentCollaborator, DocumentVersion, Comment, UserSession

def init_database():
    """Initialize database tables"""
    with app.app_context():
        try:
            print("🗄️  Creating database tables...")
            db.create_all()
            
            # Get list of created tables
            tables = db.metadata.tables.keys()
            print(f"✅ Tables created successfully!")
            print(f"📋 Tables: {', '.join(tables)}")
            
            # Verify all tables exist
            required_tables = ['users', 'documents', 'document_collaborators', 
                             'document_versions', 'comments', 'user_sessions']
            
            missing = [t for t in required_tables if t not in tables]
            if missing:
                print(f"⚠️  Warning: Some tables may be missing: {', '.join(missing)}")
                return False
            
            print("✅ All required tables verified!")
            return True
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return False

if __name__ == '__main__':
    print("=" * 50)
    print("📝 Collaborative Document Editor - Database Setup")
    print("=" * 50)
    
    if init_database():
        print("\n✅ Database setup complete!")
        print("🚀 You can now run: python app.py")
        sys.exit(0)
    else:
        print("\n❌ Database setup failed. Please check your configuration.")
        sys.exit(1)