#!/usr/bin/env python3
"""
Quick script to generate referral codes for existing users
Usage: python3 quick_referral_codes.py [--dry-run] [--limit N]
"""

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

def main():
    """Quick referral code generation"""
    # Parse command line arguments
    dry_run = '--dry-run' in sys.argv
    limit = None
    
    for arg in sys.argv:
        if arg.startswith('--limit='):
            try:
                limit = int(arg.split('=')[1])
            except ValueError:
                print("❌ Invalid limit value. Use --limit=N where N is a number")
                return
    
    print("🚀 Quick Referral Code Generation")
    print("=" * 40)
    
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made to database")
    
    if limit:
        print(f"📊 Will process maximum {limit} users")
    
    print()
    
    try:
        import db
        
        with db.get_db_connection() as cursor:
            # Get users without referral codes
            cursor.execute("""
                SELECT userId, username, email 
                FROM users 
                WHERE referral_code IS NULL OR referral_code = ''
                ORDER BY created_at ASC
            """)
            
            users = cursor.fetchall()
            
            if not users:
                print("✅ All users already have referral codes!")
                return
            
            print(f"📊 Found {len(users)} users without referral codes")
            
            if limit:
                users = users[:limit]
                print(f"📊 Processing first {len(users)} users (due to limit)")
            
            print()
            
            # Process users
            for i, user in enumerate(users, 1):
                user_id, username, email = user
                print(f"{i}. {username} ({email})")
                
                if not dry_run:
                    # Generate unique code
                    max_attempts = 50
                    referral_code = None
                    
                    for attempt in range(max_attempts):
                        code = generate_referral_code()
                        cursor.execute("SELECT COUNT(*) FROM users WHERE referral_code = %s", (code,))
                        if cursor.fetchone()[0] == 0:
                            referral_code = code
                            break
                    
                    if referral_code:
                        # Update user
                        cursor.execute("UPDATE users SET referral_code = %s WHERE userId = %s", 
                                     (referral_code, user_id))
                        print(f"   ✅ Generated: {referral_code}")
                    else:
                        print(f"   ❌ Failed to generate unique code after {max_attempts} attempts")
                else:
                    # Just show what would be generated
                    sample_code = generate_referral_code()
                    print(f"   🔍 Would generate: {sample_code}")
            
            if not dry_run:
                print(f"\n🎉 Successfully processed {len(users)} users!")
            else:
                print(f"\n🔍 Dry run completed for {len(users)} users!")
                
    except ImportError:
        print("❌ Import error. Make sure you're in the virtual environment: source .venv/bin/activate")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
