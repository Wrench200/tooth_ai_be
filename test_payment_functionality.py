#!/usr/bin/env python3
"""
Test script for payment status functionality
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8080"
TEST_BRAND_ID = "5ab69202-f66c-4298-aea1-9638174e7203"  # Replace with actual brand ID

def test_payment_functionality():
    """Test the payment status functionality"""
    
    print("🧪 Testing Payment Status Functionality")
    print("=" * 50)
    
    # Test 1: Check initial payment status
    print("\n1. Checking initial payment status...")
    try:
        response = requests.get(f"{BASE_URL}/check_brand_payment_status/{TEST_BRAND_ID}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            payment_status = response.json().get('payment_status')
            print(f"Current payment status: {payment_status}")
        else:
            print("❌ Failed to check payment status")
            return
            
    except Exception as e:
        print(f"❌ Error checking payment status: {e}")
        return
    
    # Test 2: Update payment status to True
    print("\n2. Updating payment status to True...")
    try:
        data = {
            "brandId": TEST_BRAND_ID,
            "paymentStatus": True
        }
        response = requests.post(f"{BASE_URL}/update_brand_payment_status", json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Payment status updated to True")
        else:
            print("❌ Failed to update payment status")
            return
            
    except Exception as e:
        print(f"❌ Error updating payment status: {e}")
        return
    
    # Test 3: Verify payment status was updated
    print("\n3. Verifying payment status was updated...")
    try:
        response = requests.get(f"{BASE_URL}/check_brand_payment_status/{TEST_BRAND_ID}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            payment_status = response.json().get('payment_status')
            print(f"Updated payment status: {payment_status}")
            if payment_status:
                print("✅ Payment status successfully updated to True")
            else:
                print("❌ Payment status was not updated correctly")
        else:
            print("❌ Failed to verify payment status")
            
    except Exception as e:
        print(f"❌ Error verifying payment status: {e}")
    
    # Test 4: Update payment status to False
    print("\n4. Updating payment status to False...")
    try:
        data = {
            "brandId": TEST_BRAND_ID,
            "paymentStatus": False
        }
        response = requests.post(f"{BASE_URL}/update_brand_payment_status", json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Payment status updated to False")
        else:
            print("❌ Failed to update payment status")
            
    except Exception as e:
        print(f"❌ Error updating payment status: {e}")
    
    # Test 5: Test generate_final_results with unpaid status
    print("\n5. Testing generate_final_results with unpaid status...")
    try:
        data = {
            "userId": "test-user-id",
            "brandId": TEST_BRAND_ID,
            "userName": "Test User",
            "userEmail": "test@example.com",
            "userPhoneNumbers": "1234567890",
            "registrationNumber": "REG123",
            "website": "https://example.com",
            "brandLogo": "https://example.com/logo.png",
            "others": {}
        }
        response = requests.post(f"{BASE_URL}/get_final_results", json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 400 and "Payment required" in response.json().get('message', ''):
            print("✅ Correctly blocked generation for unpaid brand")
        else:
            print("❌ Should have blocked generation for unpaid brand")
            
    except Exception as e:
        print(f"❌ Error testing generate_final_results: {e}")
    
    # Test 6: Update payment status to True and test generation
    print("\n6. Updating payment status to True and testing generation...")
    try:
        # First update payment status
        data = {
            "brandId": TEST_BRAND_ID,
            "paymentStatus": True
        }
        response = requests.post(f"{BASE_URL}/update_brand_payment_status", json=data)
        
        if response.status_code == 200:
            print("✅ Payment status updated to True")
            
            # Now test generation
            data = {
                "userId": "test-user-id",
                "brandId": TEST_BRAND_ID,
                "userName": "Test User",
                "userEmail": "test@example.com",
                "userPhoneNumbers": "1234567890",
                "registrationNumber": "REG123",
                "website": "https://example.com",
                "brandLogo": "https://example.com/logo.png",
                "others": {}
            }
            response = requests.post(f"{BASE_URL}/get_final_results", json=data)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Generation allowed for paid brand")
            else:
                print(f"❌ Generation failed: {response.json()}")
        else:
            print("❌ Failed to update payment status")
            
    except Exception as e:
        print(f"❌ Error testing generation with paid status: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Payment Status Functionality Test Complete")

if __name__ == "__main__":
    test_payment_functionality() 