#!/usr/bin/env python3
"""
Test script to debug database connection issues
"""
import os
import urllib.parse
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def test_database_url():
    """Test and fix the DATABASE_URL"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    print("=== Database URL Debug ===")
    print(f"Original DATABASE_URL: {DATABASE_URL}")
    
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL environment variable is not set!")
        return False
    
    # Check for common issues
    issues = []
    
    if 'sslmode' in DATABASE_URL and 'sslmode=' not in DATABASE_URL:
        issues.append("Malformed sslmode parameter")
    
    if 'postgresql://' not in DATABASE_URL and 'postgres://' not in DATABASE_URL:
        issues.append("Invalid database URL format")
    
    if issues:
        print(f"Found issues: {issues}")
        
        # Try to fix the URL
        fixed_url = DATABASE_URL
        
        # Fix sslmode parameter
        if 'sslmode' in fixed_url and 'sslmode=' not in fixed_url:
            fixed_url = fixed_url.replace('?sslmode&', '?sslmode=require&')
            fixed_url = fixed_url.replace('&sslmode&', '&sslmode=require&')
            fixed_url = fixed_url.replace('&sslmode', '&sslmode=require')
            if fixed_url.endswith('?sslmode'):
                fixed_url = fixed_url.replace('?sslmode', '?sslmode=require')
        
        # Ensure sslmode is set
        if 'sslmode=' not in fixed_url:
            if '?' in fixed_url:
                fixed_url += '&sslmode=require'
            else:
                fixed_url += '?sslmode=require'
        
        print(f"Fixed DATABASE_URL: {fixed_url}")
        
        # Test the fixed URL
        try:
            conn = psycopg2.connect(fixed_url)
            print("SUCCESS: Fixed URL works!")
            conn.close()
            return True
        except Exception as e:
            print(f"ERROR: Fixed URL still doesn't work: {e}")
    
    # Test original URL
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("SUCCESS: Original URL works!")
        conn.close()
        return True
    except Exception as e:
        print(f"ERROR: Original URL doesn't work: {e}")
        
        # Try parsing manually
        try:
            parsed = urllib.parse.urlparse(DATABASE_URL)
            print(f"Parsed URL components:")
            print(f"  Scheme: {parsed.scheme}")
            print(f"  Hostname: {parsed.hostname}")
            print(f"  Port: {parsed.port}")
            print(f"  Database: {parsed.path.lstrip('/')}")
            print(f"  Username: {parsed.username}")
            print(f"  Password: {'*' * len(parsed.password) if parsed.password else 'None'}")
            print(f"  Query: {parsed.query}")
            
            # Try connection with parsed parameters
            conn_params = {
                'host': parsed.hostname,
                'port': parsed.port or 5432,
                'database': parsed.path.lstrip('/'),
                'user': parsed.username,
                'password': parsed.password,
                'sslmode': 'require'
            }
            
            conn = psycopg2.connect(**conn_params)
            print("SUCCESS: Manual parsing works!")
            conn.close()
            return True
            
        except Exception as e2:
            print(f"ERROR: Manual parsing also failed: {e2}")
            return False
    
    return False

if __name__ == "__main__":
    success = test_database_url()
    if success:
        print("\n✅ Database connection test PASSED")
    else:
        print("\n❌ Database connection test FAILED")
        print("\nTroubleshooting tips:")
        print("1. Check your DATABASE_URL environment variable")
        print("2. Make sure it follows the format: postgresql://user:password@host:port/database?sslmode=require")
        print("3. Ensure all special characters in password are URL-encoded")
        print("4. Verify the database host is accessible from your deployment environment") 