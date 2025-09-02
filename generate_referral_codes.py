#!/usr/bin/env python3
"""
Script to generate referral codes for existing users in the database
"""

import os
import sys
import string
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_referral_code(length=8):
    """Generate a unique referral code"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def check_referral_code_exists(cursor, code):
    """Check if a referral code already exists in the database"""
    try:
        cursor.execute("SELECT COUNT(*) FROM users WHERE referral_code = %s", (code,))
        result = cursor.fetchone()
        return result[0] > 0 if result else False
    except Exception as e:
        print(f"Error checking referral code existence: {e}")
        return False

def generate_unique_referral_code(cursor):
    """Generate a unique referral code that doesn't exist in the database"""
    max_attempts = 100
    for attempt in range(max_attempts):
        code = generate_referral_code()
        if not check_referral_code_exists(cursor, code):
            return code
        if attempt % 20 == 0:
            print(f"Attempt {attempt + 1}: Generated code {code} already exists, trying again...")
    
    raise Exception(f"Failed to generate unique referral code after {max_attempts} attempts")

def get_users_without_referral_codes(cursor):
    """Get all users who don't have referral codes"""
    try:
        cursor.execute("""
            SELECT userId, username, email 
            FROM users 
            WHERE referral_code IS NULL OR referral_code = ''
            ORDER BY created_at ASC
        """)
        return cursor.fetchall()
    except Exception as e:
        print(f"Error getting users without referral codes: {e}")
        return []

def update_user_referral_code(cursor, user_id, referral_code):
    """Update a user's referral code"""
    try:
        cursor.execute("""
            UPDATE users 
            SET referral_code = %s 
            WHERE userId = %s
        """, (referral_code, user_id))
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating referral code for user {user_id}: {e}")
        return False

def generate_referral_codes_for_existing_users():
    """Main function to generate referral codes for existing users"""
    print("🚀 Referral Code Generation Script")
    print("=" * 50)
    
    try:
        # Import db module
        import db
        
        print("✅ Database connection successful")
        
        # Get database connection
        with db.get_db_connection() as cursor:
            print("🔍 Checking for users without referral codes...")
            
            # Get users without referral codes
            users_without_codes = get_users_without_referral_codes(cursor)
            
            if not users_without_codes:
                print("✅ All users already have referral codes!")
                return
            
            print(f"📊 Found {len(users_without_codes)} users without referral codes")
            print("\n" + "=" * 50)
            
            # Generate and assign referral codes
            successful_updates = 0
            failed_updates = 0
            
            for user in users_without_codes:
                user_id, username, email = user
                print(f"Processing user: {username} ({email})")
                
                try:
                    # Generate unique referral code
                    referral_code = generate_unique_referral_code(cursor)
                    print(f"  Generated code: {referral_code}")
                    
                    # Update user with referral code
                    if update_user_referral_code(cursor, user_id, referral_code):
                        print(f"  ✅ Successfully assigned referral code: {referral_code}")
                        successful_updates += 1
                    else:
                        print(f"  ❌ Failed to assign referral code")
                        failed_updates += 1
                        
                except Exception as e:
                    print(f"  ❌ Error processing user {username}: {e}")
                    failed_updates += 1
                
                print()  # Empty line for readability
            
            # Summary
            print("=" * 50)
            print("📊 GENERATION SUMMARY")
            print("=" * 50)
            print(f"Total users processed: {len(users_without_codes)}")
            print(f"Successful updates: {successful_updates}")
            print(f"Failed updates: {failed_updates}")
            
            if successful_updates > 0:
                print(f"\n🎉 Successfully generated referral codes for {successful_updates} users!")
                print("💡 Users can now share their referral codes with others")
            
            if failed_updates > 0:
                print(f"\n⚠️  {failed_updates} users failed to get referral codes")
                print("💡 Check the error messages above for details")
                
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the virtual environment: source .venv/bin/activate")
        return False
    except Exception as e:
        print(f"❌ Script failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def verify_referral_codes():
    """Verify that all users now have referral codes"""
    print("\n🔍 Verifying referral code generation...")
    print("=" * 50)
    
    try:
        import db
        
        with db.get_db_connection() as cursor:
            # Check total users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            # Check users with referral codes
            cursor.execute("SELECT COUNT(*) FROM users WHERE referral_code IS NOT NULL AND referral_code != ''")
            users_with_codes = cursor.fetchone()[0]
            
            # Check users without referral codes
            cursor.execute("SELECT COUNT(*) FROM users WHERE referral_code IS NULL OR referral_code = ''")
            users_without_codes = cursor.fetchone()[0]
            
            print(f"📊 Verification Results:")
            print(f"  Total users: {total_users}")
            print(f"  Users with referral codes: {users_with_codes}")
            print(f"  Users without referral codes: {users_without_codes}")
            
            if users_without_codes == 0:
                print("✅ All users now have referral codes!")
            else:
                print(f"⚠️  {users_without_codes} users still don't have referral codes")
                
            # Show some sample referral codes
            cursor.execute("""
                SELECT username, email, referral_code 
                FROM users 
                WHERE referral_code IS NOT NULL AND referral_code != ''
                ORDER BY created_at ASC
                LIMIT 5
            """)
            
            sample_users = cursor.fetchall()
            if sample_users:
                print(f"\n📝 Sample referral codes:")
                for user in sample_users:
                    username, email, code = user
                    print(f"  {username} ({email}): {code}")
                    
    except Exception as e:
        print(f"❌ Verification failed: {e}")

def main():
    """Main function"""
    print("Referral Code Generation for Existing Users")
    print("Make sure your Flask app database is accessible")
    print("=" * 50)
    
    try:
        # Generate referral codes
        success = generate_referral_codes_for_existing_users()
        
        if success:
            # Verify the results
            verify_referral_codes()
            
            print("\n🎉 Script completed successfully!")
            print("💡 All existing users now have referral codes")
        else:
            print("\n❌ Script failed!")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Script interrupted by user")
    except Exception as e:
        print(f"\n❌ Script failed with error: {e}")
        print("💡 Check the error messages above for details")

if __name__ == "__main__":
    main()
