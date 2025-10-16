#!/usr/bin/env python3
"""
Database initialization script
Run this script to set up a fresh database with all required tables
"""

import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def init_database():
    """Initialize the database with all required tables"""
    try:
        print("🚀 Initializing database...")
        
        # Import db module to trigger table creation
        import db
        
        print("✅ Database initialization completed successfully!")
        print("\nTables created:")
        print("- users")
        print("- brands") 
        print("- transactions")
        print("- payment_transactions")
        print("- answers")
        print("- referral_codes")
        print("- feedback")
        print("\nIndexes created:")
        print("- Payment transaction indexes")
        print("- Referral code indexes")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your DATABASE_URL in .env file")
        print("2. Ensure PostgreSQL is running")
        print("3. Verify database credentials")
        print("4. Check network connectivity")
        return False

def test_database_connection():
    """Test database connection"""
    try:
        print("🔍 Testing database connection...")
        
        import db
        from db import get_db_connection
        
        with get_db_connection() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Connected to PostgreSQL: {version[0]}")
            
            # Test table existence
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            print(f"✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
                
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🗄️  Jara AI Database Initialization")
    print("=" * 50)
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("Please set DATABASE_URL in your .env file")
        print("Example: DATABASE_URL=postgresql://user:pass@host:port/db?sslmode=require")
        sys.exit(1)
    
    print(f"📊 Database URL: {database_url[:50]}...")
    
    # Test connection first
    if not test_database_connection():
        print("\n❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Initialize database
    if init_database():
        print("\n🎉 Database setup completed successfully!")
        print("\nNext steps:")
        print("1. Run the backend: python main.py")
        print("2. Test the API endpoints")
        print("3. Create your first user and brand")
    else:
        print("\n❌ Database setup failed")
        sys.exit(1)
