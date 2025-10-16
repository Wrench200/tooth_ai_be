#!/usr/bin/env python3
"""
Test script for Fapshi payment integration
"""

import requests
import json
import uuid

# Configuration
BASE_URL = "http://localhost:8090"
TEST_BRAND_ID = "test-brand-123"

def test_initiate_payment():
    """Test initiating a payment"""
    print("=== Testing Payment Initiation ===")
    
    # Test data
    test_data = {
        "amount": 15000,  # Amount in XAF
        "brandId": TEST_BRAND_ID,
        "email": "test@example.com",
        "redirectUrl": "https://example.com/payment-success",
        "userId": "test-user-123",
        "message": "Test payment for brand kit"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/payment/initiate", json=test_data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("✅ Payment initiated successfully!")
                print(f"Payment Link: {result.get('data', {}).get('link', 'N/A')}")
                print(f"External ID: {result.get('external_id', 'N/A')}")
                return result
            else:
                print("❌ Payment initiation failed!")
                print(f"Error: {result.get('error')}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_verify_payment(trans_id):
    """Test verifying a payment"""
    print(f"\n=== Testing Payment Verification ===")
    print(f"Transaction ID: {trans_id}")
    
    test_data = {
        "transId": trans_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/payment/verify", json=test_data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                if result.get('verified'):
                    print("✅ Payment verified successfully!")
                    payment_data = result.get('payment_data', {})
                    print(f"Status: {payment_data.get('status')}")
                    print(f"Amount: {payment_data.get('amount')} XAF")
                else:
                    print("⚠️  Payment verification failed or pending")
                    print(f"Error: {result.get('error')}")
                return result
            else:
                print("❌ Payment verification failed!")
                print(f"Error: {result.get('error')}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_get_payment_status(trans_id):
    """Test getting payment status"""
    print(f"\n=== Testing Payment Status Check ===")
    print(f"Transaction ID: {trans_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/payment/status?transId={trans_id}")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("✅ Payment status retrieved successfully!")
                payment_data = result.get('payment_data', {})
                print(f"Status: {payment_data.get('status')}")
                return result
            else:
                print("❌ Payment status check failed!")
                print(f"Error: {result.get('error')}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_payment_callback():
    """Test payment callback"""
    print(f"\n=== Testing Payment Callback ===")
    
    # Simulate a successful payment callback
    callback_data = {
        "transId": "TEST123456",
        "status": "SUCCESSFUL",
        "amount": 15000,
        "externalId": f"brand_ai_{TEST_BRAND_ID}_abc123",
        "currency": "XAF",
        "payerName": "Test User",
        "email": "test@example.com"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/payment/callback", json=callback_data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("✅ Payment callback processed successfully!")
                return result
            else:
                print("❌ Payment callback failed!")
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
    """Test brand payment status endpoints"""
    print(f"\n=== Testing Brand Payment Status ===")
    
    # Test checking payment status
    try:
        response = requests.get(f"{BASE_URL}/check_brand_payment_status/{TEST_BRAND_ID}")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("✅ Brand payment status retrieved successfully!")
                print(f"Payment Status: {result.get('payment_status')}")
                return result
            else:
                print("❌ Brand payment status check failed!")
                print(f"Error: {result.get('message')}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_payment_transactions():
    """Test payment transaction database endpoints"""
    print(f"\n=== Testing Payment Transactions ===")
    
    # Test getting transactions by brand
    try:
        response = requests.get(f"{BASE_URL}/api/payment/transactions/{TEST_BRAND_ID}")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("✅ Payment transactions retrieved successfully!")
                print(f"Transaction Count: {result.get('count')}")
                return result
            else:
                print("❌ Payment transactions retrieval failed!")
                print(f"Error: {result.get('error')}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_payment_transaction_by_id():
    """Test getting a specific payment transaction"""
    print(f"\n=== Testing Payment Transaction by ID ===")
    
    # Test with a sample external_id
    test_external_id = f"brand_ai_{TEST_BRAND_ID}_test123"
    
    try:
        response = requests.get(f"{BASE_URL}/api/payment/transaction/{test_external_id}")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("✅ Payment transaction retrieved successfully!")
                return result
            else:
                print("❌ Payment transaction retrieval failed!")
                print(f"Error: {result.get('error')}")
                return None
        elif response.status_code == 404:
            print("⚠️  Payment transaction not found (expected for test)")
            return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

if __name__ == "__main__":
    print("=== Fapshi Payment Integration Test ===")
    print("Make sure your Flask app is running on http://localhost:8080")
    print("Make sure Fapshi API credentials are set in environment variables")
    print("=" * 50)
    
    try:
        # Test 1: Initiate payment
        print("\n1. Testing payment initiation...")
        payment_result = test_initiate_payment()
        
        if payment_result and payment_result.get('success'):
            # Extract transaction ID from the response
            payment_data = payment_result.get('data', {})
            trans_id = payment_data.get('transId')
            
            if trans_id:
                # Test 2: Get payment status
                print("\n2. Testing payment status check...")
                test_get_payment_status(trans_id)
                
                # Test 3: Verify payment (this will likely fail in test environment)
                print("\n3. Testing payment verification...")
                test_verify_payment(trans_id)
            else:
                print("⚠️  No transaction ID returned from payment initiation")
        
        # Test 4: Test payment callback
        print("\n4. Testing payment callback...")
        test_payment_callback()
        
        # Test 5: Test brand payment status
        print("\n5. Testing brand payment status...")
        test_brand_payment_status()
        
        # Test 6: Test payment transactions database
        print("\n6. Testing payment transactions database...")
        test_payment_transactions()
        
        # Test 7: Test specific payment transaction
        print("\n7. Testing specific payment transaction...")
        test_payment_transaction_by_id()
        
        print("\n" + "=" * 50)
        print("🏁 Fapshi Payment Integration Test Complete")
        print("\nTo complete a real payment:")
        print("1. Call /api/payment/initiate with real customer data")
        print("2. Redirect customer to the payment link")
        print("3. Customer completes payment on Fapshi")
        print("4. Payment status is automatically updated via callback")
        print("5. Or manually verify using /api/payment/verify")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("💡 Make sure your Flask app is running and Fapshi credentials are set")
