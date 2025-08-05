#!/usr/bin/env python3
"""
Simple test to check if the database functions work
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test if we can import the db module"""
    try:
        import db
        print("✅ db module imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import db module: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    try:
        import db
        # Test the connection
        result = db.test_connection()
        if result:
            print("✅ Database connection test successful")
            return True
        else:
            print("❌ Database connection test failed")
            return False
    except Exception as e:
        print(f"❌ Database connection test error: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Database Functions ===")
    
    # Test import
    import_success = test_import()
    
    if import_success:
        # Test database connection
        connection_success = test_database_connection()
        
        print("\n=== Test Summary ===")
        print(f"Import: {'✅ PASS' if import_success else '❌ FAIL'}")
        print(f"Connection: {'✅ PASS' if connection_success else '❌ FAIL'}")
    else:
        print("\n=== Test Summary ===")
        print(f"Import: {'✅ PASS' if import_success else '❌ FAIL'}")
        print("Connection: ❌ SKIP (import failed)") 