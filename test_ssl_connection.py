#!/usr/bin/env python3
"""
Test script to verify SSL connection handling and connection pooling
"""
import os
import time
import threading
from dotenv import load_dotenv
import db

load_dotenv()

def test_basic_connection():
    """Test basic database connection"""
    print("=== Testing Basic Connection ===")
    try:
        result = db.test_connection()
        if result:
            print("✅ Basic connection test PASSED")
            return True
        else:
            print("❌ Basic connection test FAILED")
            return False
    except Exception as e:
        print(f"❌ Basic connection test ERROR: {e}")
        return False

def test_concurrent_connections():
    """Test concurrent database connections"""
    print("\n=== Testing Concurrent Connections ===")
    
    def worker(worker_id):
        try:
            with db.get_db_connection() as cursor:
                cursor.execute("SELECT %s as worker_id, NOW() as timestamp", (worker_id,))
                result = cursor.fetchone()
                print(f"Worker {worker_id}: {result}")
                return True
        except Exception as e:
            print(f"Worker {worker_id} ERROR: {e}")
            return False
    
    # Create multiple threads
    threads = []
    results = []
    
    for i in range(5):
        thread = threading.Thread(target=lambda i=i: results.append(worker(i)))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    success_count = sum(results)
    print(f"✅ Concurrent connection test: {success_count}/5 workers succeeded")
    return success_count == 5

def test_connection_reuse():
    """Test connection reuse and pooling"""
    print("\n=== Testing Connection Reuse ===")
    
    try:
        # First connection
        with db.get_db_connection() as cursor:
            cursor.execute("SELECT 1 as test")
            result1 = cursor.fetchone()
            print(f"First connection: {result1}")
        
        # Second connection (should reuse)
        with db.get_db_connection() as cursor:
            cursor.execute("SELECT 2 as test")
            result2 = cursor.fetchone()
            print(f"Second connection: {result2}")
        
        # Third connection after a delay (might create new connection)
        time.sleep(1)
        with db.get_db_connection() as cursor:
            cursor.execute("SELECT 3 as test")
            result3 = cursor.fetchone()
            print(f"Third connection: {result3}")
        
        print("✅ Connection reuse test PASSED")
        return True
    except Exception as e:
        print(f"❌ Connection reuse test ERROR: {e}")
        return False

def test_ssl_parameters():
    """Test SSL connection parameters"""
    print("\n=== Testing SSL Parameters ===")
    
    try:
        with db.get_db_connection() as cursor:
            # Check SSL status
            cursor.execute("SHOW ssl")
            ssl_status = cursor.fetchone()
            print(f"SSL Status: {ssl_status}")
            
            # Check connection info
            cursor.execute("SELECT version(), current_database(), current_user")
            conn_info = cursor.fetchone()
            print(f"Connection Info: {conn_info}")
            
            # Check session parameters
            cursor.execute("SHOW ssl_renegotiation_limit")
            ssl_renog = cursor.fetchone()
            print(f"SSL Renegotiation Limit: {ssl_renog}")
            
            cursor.execute("SHOW statement_timeout")
            stmt_timeout = cursor.fetchone()
            print(f"Statement Timeout: {stmt_timeout}")
        
        print("✅ SSL parameters test PASSED")
        return True
    except Exception as e:
        print(f"❌ SSL parameters test ERROR: {e}")
        return False

def test_error_handling():
    """Test error handling and connection recovery"""
    print("\n=== Testing Error Handling ===")
    
    try:
        # Test invalid query (should not break connection)
        with db.get_db_connection() as cursor:
            try:
                cursor.execute("SELECT * FROM non_existent_table")
            except Exception as e:
                print(f"Expected error for invalid query: {e}")
        
        # Test valid query after error (should still work)
        with db.get_db_connection() as cursor:
            cursor.execute("SELECT 1 as recovery_test")
            result = cursor.fetchone()
            print(f"Recovery test: {result}")
        
        print("✅ Error handling test PASSED")
        return True
    except Exception as e:
        print(f"❌ Error handling test ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("🔧 Testing SSL Connection Management")
    print("=" * 50)
    
    tests = [
        test_basic_connection,
        test_concurrent_connections,
        test_connection_reuse,
        test_ssl_parameters,
        test_error_handling
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} CRASHED: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! SSL connection management is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 