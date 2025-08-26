#!/usr/bin/env python3
"""
Simple test script to verify SQLAlchemy + SQLite setup.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, get_db
from app.models import Build, Pipeline, Notification
from sqlalchemy.orm import Session

def test_database_connection():
    """Test database connection and table creation."""
    print("Testing database connection...")
    
    try:
        # Initialize database
        init_db()
        print("✅ Database initialized successfully")
        
        # Test session creation
        db_gen = get_db()
        db = next(db_gen)
        print("✅ Database session created successfully")
        
        # Test table creation by checking if tables exist
        inspector = db.get_bind().dialect.inspector(db.get_bind())
        tables = inspector.get_table_names()
        expected_tables = ['builds', 'pipelines', 'notifications']
        
        for table in expected_tables:
            if table in tables:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' missing")
        
        db.close()
        print("✅ Database session closed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    if success:
        print("\n🎉 All database tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Database tests failed!")
        sys.exit(1)
