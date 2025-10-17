#!/usr/bin/env python3
"""
Database connection test script
Test the improved database connection handling
"""

import os
import sys
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test the database connection with the improved manager"""
    print("=" * 60)
    print("🗄️  Database Connection Test")
    print("=" * 60)
    
    try:
        # Import the database module
        import db
        
        # Get database info
        print("\n📊 Database Information:")
        db_info = db.get_database_info()
        if db_info:
            print(f"  Host: {db_info['host']}")
            print(f"  Port: {db_info['port']}")
            print(f"  Database: {db_info['database']}")
            print(f"  User: {db_info['user']}")
            print(f"  SSL Mode: {db_info['ssl_mode']}")
        else:
            print("  ❌ Could not get database information")
            return False
        
        # Test basic connection
        print("\n🔍 Testing Basic Connection:")
        try:
            with db.get_db_connection() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()
                print(f"  ✅ Connected to: {version[0]}")
        except Exception as e:
            print(f"  ❌ Connection failed: {e}")
            return False
        
        # Test health check
        print("\n🏥 Testing Health Check:")
        is_healthy = db.check_database_health()
        if is_healthy:
            print("  ✅ Database health check passed")
        else:
            print("  ❌ Database health check failed")
            return False
        
        # Test multiple connections
        print("\n🔄 Testing Multiple Connections:")
        for i in range(3):
            try:
                with db.get_db_connection() as cursor:
                    cursor.execute("SELECT 1 as test_connection")
                    result = cursor.fetchone()
                    if result and result[0] == 1:
                        print(f"  ✅ Connection {i+1}: Success")
                    else:
                        print(f"  ❌ Connection {i+1}: Failed")
                        return False
            except Exception as e:
                print(f"  ❌ Connection {i+1}: Error - {e}")
                return False
        
        # Test connection resilience
        print("\n🛡️  Testing Connection Resilience:")
        try:
            # Force a connection reset
            db.reset_connection()
            print("  ✅ Connection reset successful")
            
            # Test after reset
            with db.get_db_connection() as cursor:
                cursor.execute("SELECT 'resilience_test' as test")
                result = cursor.fetchone()
                if result and result[0] == 'resilience_test':
                    print("  ✅ Connection after reset: Success")
                else:
                    print("  ❌ Connection after reset: Failed")
                    return False
        except Exception as e:
            print(f"  ❌ Resilience test failed: {e}")
            return False
        
        print("\n🎉 All database connection tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Could not import database module: {e}")
        print("Make sure you're in the backend directory and all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during testing: {e}")
        return False

def test_database_operations():
    """Test basic database operations"""
    print("\n" + "=" * 60)
    print("🔧 Database Operations Test")
    print("=" * 60)
    
    try:
        import db
        
        # Test table existence
        print("\n📋 Testing Table Existence:")
        with db.get_db_connection() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            expected_tables = ['users', 'brands', 'answers', 'transactions', 'payment_transactions']
            found_tables = [table[0] for table in tables]
            
            print(f"  Found {len(tables)} tables:")
            for table in found_tables:
                print(f"    - {table}")
            
            missing_tables = [table for table in expected_tables if table not in found_tables]
            if missing_tables:
                print(f"  ⚠️  Missing expected tables: {missing_tables}")
            else:
                print("  ✅ All expected tables found")
        
        # Test user table structure
        print("\n👥 Testing User Table:")
        with db.get_db_connection() as cursor:
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            
            print(f"  User table has {len(columns)} columns:")
            for col_name, col_type in columns:
                print(f"    - {col_name}: {col_type}")
        
        print("\n✅ Database operations test completed")
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Database Connection Tests...")
    
    # Check if DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL not found in environment variables")
        print("Please set DATABASE_URL in your .env file")
        sys.exit(1)
    
    # Run tests
    connection_test_passed = test_database_connection()
    operations_test_passed = test_database_operations()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"Connection Test: {'✅ PASSED' if connection_test_passed else '❌ FAILED'}")
    print(f"Operations Test: {'✅ PASSED' if operations_test_passed else '❌ FAILED'}")
    
    if connection_test_passed and operations_test_passed:
        print("\n🎉 All tests passed! Database connection is working properly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the database configuration.")
        sys.exit(1)
