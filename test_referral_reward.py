#!/usr/bin/env python3
"""
Test script for referral reward functionality in update_brand_payment_status endpoint
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_referral_reward():
    """Test referral reward processing when payment status is updated"""
    print("🚀 Testing Referral Reward System")
    print("=" * 50)
    
    # Test 1: Create referrer user
    print("\n1. Creating referrer user...")
    referrer_data = {
        "userName": "ReferrerUser",
        "email": "referrer@test.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register_user", json=referrer_data)
        if response.status_code == 201:
            referrer = response.json()['user']
            print(f"✅ Referrer created: {referrer['username']} (ID: {referrer['id']})")
        else:
            print(f"❌ Failed to create referrer: {response.status_code}")
            print(f"   Response: {response.json()}")
            return
    except Exception as e:
        print(f"❌ Error creating referrer: {e}")
        return
    
    # Wait for database update
    time.sleep(1)
    
    # Test 2: Get referrer's initial stats
    print("\n2. Getting referrer's initial stats...")
    try:
        response = requests.get(f"{BASE_URL}/referral/stats/{referrer['id']}")
        if response.status_code == 200:
            initial_stats = response.json()['stats']
            print(f"✅ Initial referral stats:")
            print(f"   Referred Users: {initial_stats['referred_users']}")
            print(f"   Referred Amount: ₦{initial_stats['referred_amount']}")
        else:
            print(f"❌ Failed to get initial stats: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting initial stats: {e}")
        return
    
    # Test 3: Create referred user
    print("\n3. Creating referred user...")
    referred_data = {
        "userName": "ReferredUser",
        "email": "referred@test.com",
        "password": "testpass123",
        "referralCode": initial_stats['referral_code']
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register_user", json=referred_data)
        if response.status_code == 201:
            referred = response.json()['user']
            print(f"✅ Referred user created: {referred['username']} (ID: {referred['id']})")
        else:
            print(f"❌ Failed to create referred user: {response.status_code}")
            print(f"   Response: {response.json()}")
            return
    except Exception as e:
        print(f"❌ Error creating referred user: {e}")
        return
    
    # Wait for database update
    time.sleep(1)
    
    # Test 4: Create a brand for the referred user
    print("\n4. Creating brand for referred user...")
    try:
        response = requests.post(f"{BASE_URL}/create_brand", json={"userId": referred['id']})
        if response.status_code == 201:
            brand = response.json()['brand']
            print(f"✅ Brand created: {brand['id']}")
        else:
            print(f"❌ Failed to create brand: {response.status_code}")
            print(f"   Response: {response.json()}")
            return
    except Exception as e:
        print(f"❌ Error creating brand: {e}")
        return
    
    # Test 5: Update payment status (this should trigger referral reward)
    print("\n5. Updating payment status (should trigger referral reward)...")
    payment_data = {
        "brandId": brand['id'],
        "paymentStatus": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/update_brand_payment_status", json=payment_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Payment status updated: {result['message']}")
            
            # Check if referral message is included
            if "Referral reward" in result['message']:
                print("🎉 Referral reward processed successfully!")
            else:
                print("⚠️  No referral reward message found")
        else:
            print(f"❌ Failed to update payment status: {response.status_code}")
            print(f"   Response: {response.json()}")
            return
    except Exception as e:
        print(f"❌ Error updating payment status: {e}")
        return
    
    # Wait for database update
    time.sleep(1)
    
    # Test 6: Check updated referral stats
    print("\n6. Checking updated referral stats...")
    try:
        response = requests.get(f"{BASE_URL}/referral/stats/{referrer['id']}")
        if response.status_code == 200:
            updated_stats = response.json()['stats']
            print(f"✅ Updated referral stats:")
            print(f"   Referred Users: {updated_stats['referred_users']} (was {initial_stats['referred_users']})")
            print(f"   Referred Amount: ₦{updated_stats['referred_amount']} (was ₦{initial_stats['referred_amount']})")
            
            # Check if both fields increased correctly
            users_increase = updated_stats['referred_users'] - initial_stats['referred_users']
            amount_increase = updated_stats['referred_amount'] - initial_stats['referred_amount']
            
            if users_increase == 1 and amount_increase == 1000:
                print("🎉 Referral reward processed successfully!")
                print("   ✅ Referred users count incremented by 1")
                print("   ✅ Referral amount increased by ₦1,000")
            else:
                print(f"⚠️  Users increase: {users_increase} (expected 1)")
                print(f"⚠️  Amount increase: ₦{amount_increase} (expected ₦1,000)")
        else:
            print(f"❌ Failed to get updated stats: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting updated stats: {e}")
    
    print("\n🎉 Referral reward test completed!")
    print("💡 Check the results above to verify the referral reward system")

if __name__ == "__main__":
    print("Referral Reward Test")
    print("Make sure your Flask app is running on http://localhost:5000")
    print("=" * 50)
    
    try:
        test_referral_reward()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("💡 Make sure your Flask app is running and database is accessible")
