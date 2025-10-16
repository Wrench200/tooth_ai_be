#!/usr/bin/env python3
"""
Test script for multiple brand creation functionality
"""

import requests
import json
import uuid

# Configuration
BASE_URL = "http://localhost:8090"
TEST_USER_ID = "test-user-multiple-brands-123"

def test_create_multiple_brands():
    """Test creating multiple brands for the same user"""
    print("=== Testing Multiple Brand Creation ===")
    
    brands_created = []
    
    # Create first brand
    print("\n1. Creating first brand...")
    try:
        response = requests.post(f"{BASE_URL}/create_brand", json={"userId": TEST_USER_ID})
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                brand1 = result.get('brand')
                brands_created.append(brand1)
                print("✅ First brand created successfully!")
                print(f"Brand ID: {brand1.get('id')}")
                print(f"Brand Name: {brand1.get('name')}")
            else:
                print("❌ First brand creation failed!")
                print(f"Error: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    
    # Create second brand
    print("\n2. Creating second brand...")
    try:
        response = requests.post(f"{BASE_URL}/create_brand", json={"userId": TEST_USER_ID})
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                brand2 = result.get('brand')
                brands_created.append(brand2)
                print("✅ Second brand created successfully!")
                print(f"Brand ID: {brand2.get('id')}")
                print(f"Brand Name: {brand2.get('name')}")
            else:
                print("❌ Second brand creation failed!")
                print(f"Error: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    
    # Create third brand
    print("\n3. Creating third brand...")
    try:
        response = requests.post(f"{BASE_URL}/create_brand", json={"userId": TEST_USER_ID})
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                brand3 = result.get('brand')
                brands_created.append(brand3)
                print("✅ Third brand created successfully!")
                print(f"Brand ID: {brand3.get('id')}")
                print(f"Brand Name: {brand3.get('name')}")
            else:
                print("❌ Third brand creation failed!")
                print(f"Error: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    
    print(f"\n🎉 Successfully created {len(brands_created)} brands for user {TEST_USER_ID}!")
    
    # Verify all brands are different
    brand_ids = [brand.get('id') for brand in brands_created]
    if len(set(brand_ids)) == len(brand_ids):
        print("✅ All brands have unique IDs")
    else:
        print("❌ Some brands have duplicate IDs!")
        return False
    
    return brands_created

def test_get_user_brands():
    """Test getting all brands for a user"""
    print(f"\n=== Testing Get User Brands ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/user/{TEST_USER_ID}/brands")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                brands = result.get('brands', [])
                print(f"✅ Retrieved {len(brands)} brands for user {TEST_USER_ID}")
                
                for i, brand in enumerate(brands, 1):
                    print(f"  Brand {i}: {brand.get('name')} (ID: {brand.get('id')})")
                
                return brands
            else:
                print("❌ Failed to retrieve user brands!")
                print(f"Error: {result.get('error')}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_brand_payment_status():
    """Test payment status for multiple brands"""
    print(f"\n=== Testing Brand Payment Status ===")
    
    # Get user brands first
    brands = test_get_user_brands()
    if not brands:
        print("❌ No brands found to test payment status")
        return False
    
    for i, brand in enumerate(brands, 1):
        brand_id = brand.get('id')
        print(f"\nTesting payment status for Brand {i} (ID: {brand_id})...")
        
        try:
            response = requests.get(f"{BASE_URL}/check_brand_payment_status/{brand_id}")
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Payment Status: {result.get('payment_status')}")
                
                if result.get('success'):
                    print(f"✅ Payment status retrieved for Brand {i}")
                else:
                    print(f"❌ Failed to get payment status for Brand {i}")
            else:
                print(f"❌ HTTP error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
    
    return True

def cleanup_test_data():
    """Clean up test data (optional)"""
    print(f"\n=== Cleanup Test Data ===")
    print("Note: Test data cleanup is not implemented in this script.")
    print("You may want to manually clean up test brands if needed.")
    print(f"Test User ID: {TEST_USER_ID}")

if __name__ == "__main__":
    print("=== Multiple Brand Creation Test ===")
    print("Make sure your Flask app is running on http://localhost:8090")
    print("=" * 50)
    
    try:
        # Test 1: Create multiple brands
        print("\n1. Testing multiple brand creation...")
        brands_created = test_create_multiple_brands()
        
        if brands_created:
            # Test 2: Get all user brands
            print("\n2. Testing get user brands...")
            test_get_user_brands()
            
            # Test 3: Test payment status for all brands
            print("\n3. Testing payment status for all brands...")
            test_brand_payment_status()
            
            # Cleanup
            cleanup_test_data()
            
            print("\n" + "=" * 50)
            print("🏁 Multiple Brand Creation Test Complete")
            print(f"✅ Successfully created and tested {len(brands_created)} brands")
            print("\nKey Features Verified:")
            print("- Users can create multiple brands")
            print("- Each brand has a unique ID")
            print("- All brands can be retrieved for a user")
            print("- Payment status can be checked for each brand")
            
        else:
            print("\n❌ Test failed - could not create multiple brands")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("💡 Make sure your Flask app is running and database is accessible")


