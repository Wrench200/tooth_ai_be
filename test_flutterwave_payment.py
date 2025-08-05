#!/usr/bin/env python3
"""
Test script for Flutterwave payment integration
"""

import requests
import json
import uuid

# Configuration
BASE_URL = "http://127.0.0.1:8080"

def test_initiate_payment():
    """Test initiating a payment"""
    print("=== Testing Payment Initiation ===")
    
    # Test data
    test_data = {
        "amount": 5000,  # Amount in kobo (50 NGN)
        "email": "test@example.com",
        "phone_number": "+2348012345678",
        "name": "John Doe",
        "brand_id": "d14811d2-cc1f-4170-bbc5-17ddf895498d",
        "currency": "NGN"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/payment/initiate", json=test_data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("✅ Payment initiated successfully!")
                print(f"Payment URL: {result.get('payment_url')}")
                print(f"Transaction Reference: {result.get('tx_ref')}")
                return result
            else:
                print("❌ Payment initiation failed!")
                print(f"Error: {result.get('message')}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_verify_payment(transaction_id):
    """Test verifying a payment"""
    print(f"\n=== Testing Payment Verification ===")
    print(f"Transaction ID: {transaction_id}")
    
    test_data = {
        "transaction_id": transaction_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/payment/verify", json=test_data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("✅ Payment verified successfully!")
                payment_data = result.get('payment_data', {})
                print(f"Status: {payment_data.get('status')}")
                print(f"Amount: {payment_data.get('amount')} {payment_data.get('currency')}")
                return result
            else:
                print("❌ Payment verification failed!")
                print(f"Error: {result.get('message')}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_check_payment_status(brand_id):
    """Test checking payment status"""
    print(f"\n=== Testing Payment Status Check ===")
    print(f"Brand ID: {brand_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/check_brand_payment_status/{brand_id}")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("✅ Payment status retrieved successfully!")
                print(f"Payment Status: {result.get('payment_status')}")
                return result
            else:
                print("❌ Payment status check failed!")
                print(f"Error: {result.get('message')}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_update_payment_status(brand_id, status):
    """Test updating payment status"""
    print(f"\n=== Testing Payment Status Update ===")
    print(f"Brand ID: {brand_id}")
    print(f"Status: {status}")
    
    test_data = {
        "brandId": brand_id,
        "paymentStatus": status
    }
    
    try:
        response = requests.post(f"{BASE_URL}/update_brand_payment_status", json=test_data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("✅ Payment status updated successfully!")
                return result
            else:
                print("❌ Payment status update failed!")
                print(f"Error: {result.get('message')}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

if __name__ == "__main__":
    print("=== Flutterwave Payment Integration Test ===")
    
    # Test brand ID
    test_brand_id = "d14811d2-cc1f-4170-bbc5-17ddf895498d"
    
    # Test 1: Check initial payment status
    print("\n1. Checking initial payment status...")
    initial_status = test_check_payment_status(test_brand_id)
    
    # Test 2: Initiate payment
    print("\n2. Initiating payment...")
    payment_result = test_initiate_payment()
    
    if payment_result:
        print("\n3. Payment initiated! You can:")
        print("   - Visit the payment URL to complete payment")
        print("   - Use the transaction reference for verification")
        print("   - Check the webhook endpoint for automatic updates")
    
    # Test 3: Update payment status manually (for testing)
    print("\n4. Testing manual payment status update...")
    test_update_payment_status(test_brand_id, True)
    
    # Test 4: Check updated payment status
    print("\n5. Checking updated payment status...")
    updated_status = test_check_payment_status(test_brand_id)
    
    # Test 5: Reset payment status (for testing)
    print("\n6. Resetting payment status for testing...")
    test_update_payment_status(test_brand_id, False)
    
    print("\n=== Test Summary ===")
    print("✅ Payment integration test completed!")
    print("\nTo complete a real payment:")
    print("1. Call /payment/initiate with real customer data")
    print("2. Redirect customer to the payment_url")
    print("3. Customer completes payment on Flutterwave")
    print("4. Payment status is automatically updated via webhook")
    print("5. Or manually verify using /payment/verify") 