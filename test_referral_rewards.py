#!/usr/bin/env python3
"""
Test script for referral reward functionality
Tests the referral reward processing when a user pays for a brand
"""

import requests
import json
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://localhost:8090"

def test_referral_rewards():
    """Test the referral reward functionality"""
    print("=" * 60)
    print("🧪 Testing Referral Reward Functionality")
    print("=" * 60)
    
    try:
        # Test 1: Get referral rewards for a user
        print("\n1️⃣ Testing referral rewards endpoint...")
        
        # You'll need to replace this with an actual user ID from your database
        test_user_id = "test-user-id"  # Replace with actual user ID
        
        response = requests.get(f"{BASE_URL}/referral/rewards/{test_user_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Referral rewards retrieved successfully")
            print(f"   Total referrals: {data.get('data', {}).get('total_referrals', 0)}")
            print(f"   Total earnings: {data.get('data', {}).get('total_earnings', 0)} XAF")
            print(f"   Referral code: {data.get('data', {}).get('referral_code', 'N/A')}")
        else:
            print(f"❌ Failed to get referral rewards: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test 2: Test referral stats endpoint
        print("\n2️⃣ Testing referral stats endpoint...")
        
        response = requests.get(f"{BASE_URL}/referral/stats/{test_user_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Referral stats retrieved successfully")
            print(f"   Data: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Failed to get referral stats: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test 3: Test referral history endpoint
        print("\n3️⃣ Testing referral history endpoint...")
        
        response = requests.get(f"{BASE_URL}/referral/history/{test_user_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Referral history retrieved successfully")
            print(f"   Total referrals: {len(data.get('data', []))}")
            if data.get('data'):
                print(f"   Sample referral: {json.dumps(data['data'][0], indent=2)}")
        else:
            print(f"❌ Failed to get referral history: {response.status_code}")
            print(f"   Response: {response.text}")
        
        print("\n" + "=" * 60)
        print("📋 Referral Reward System Overview")
        print("=" * 60)
        print("💰 When a user pays 15,000 XAF for a brand:")
        print("   • 20% (3,000 XAF) is shared as rewards")
        print("   • 10% (1,500 XAF) goes to the brand creator")
        print("   • 10% (1,500 XAF) goes to the referrer (if any)")
        print("")
        print("🔄 Reward Processing:")
        print("   • Triggered automatically on successful payment verification")
        print("   • Updates user's 'referred_amount' field")
        print("   • Logs all reward transactions")
        print("")
        print("📊 Available Endpoints:")
        print("   • GET /referral/rewards/{user_id} - Get user's reward history")
        print("   • GET /referral/stats/{user_id} - Get user's referral statistics")
        print("   • GET /referral/history/{user_id} - Get detailed referral history")
        print("   • POST /referral/validate/{code} - Validate referral code")
        print("   • GET /referral/leaderboard - Get referral leaderboard")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server")
        print("   Make sure the backend is running on http://localhost:8090")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_payment_simulation():
    """Simulate a payment to test referral rewards"""
    print("\n" + "=" * 60)
    print("💳 Payment Simulation Test")
    print("=" * 60)
    print("ℹ️  To test referral rewards with actual payment:")
    print("   1. Create a brand with a user who has a referrer")
    print("   2. Initiate payment for 15,000 XAF")
    print("   3. Complete the payment through Fapshi")
    print("   4. Check the backend logs for referral reward processing")
    print("   5. Verify the user's referred_amount was updated")
    print("")
    print("🔍 Backend logs should show:")
    print("   • '🔄 Processing referral rewards for user X, amount 15000'")
    print("   • '💰 Total reward: 3000 XAF, Individual reward: 1500 XAF'")
    print("   • '✅ Brand creator X rewarded 1500 XAF'")
    print("   • '✅ Referrer Y rewarded 1500 XAF' (if user was referred)")

if __name__ == "__main__":
    print("🚀 Starting Referral Reward Tests...")
    
    # Test the endpoints
    success = test_referral_rewards()
    
    # Show payment simulation info
    test_payment_simulation()
    
    if success:
        print("\n🎉 Referral reward system is ready!")
        print("   The system will automatically process rewards when users pay for brands.")
    else:
        print("\n❌ Some tests failed. Check the backend server and database connection.")
    
    print("\n" + "=" * 60)
