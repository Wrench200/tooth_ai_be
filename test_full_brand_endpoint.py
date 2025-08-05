#!/usr/bin/env python3
"""
Test script for the new /get_full_brand endpoint
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8080"  # Change this to your server URL
TEST_BRAND_ID = "5ab69202-f66c-4298-aea1-9638174e7203"  # Real brand ID from your database

def test_get_full_brand():
    """Test the get_full_brand endpoint"""
    
    print("Testing /get_full_brand endpoint...")
    print("=" * 50)
    
    # Test 1: Valid request
    print("Test 1: Valid brand ID request")
    try:
        response = requests.get(
            f"{BASE_URL}/get_full_brand/{TEST_BRAND_ID}"
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('full_brand'):
                full_brand = data['full_brand']
                print("\n✅ Success! Full brand data structure:")
                print(f"  - Brand data: {list(full_brand.get('brand', {}).keys())}")
                print(f"  - Brand assets: {'Present' if full_brand.get('brand_assets') else 'None'}")
            else:
                print("❌ Request succeeded but no brand data returned")
        else:
            print("❌ Request failed")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure the server is running")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    
    # Test 2: Missing brandId
    print("Test 2: Missing brandId")
    try:
        response = requests.get(
            f"{BASE_URL}/get_full_brand/"
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400:
            print("✅ Correctly returned 400 for missing brandId")
        else:
            print("❌ Expected 400 status code")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure the server is running")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    
    # Test 3: Invalid brand ID
    print("Test 3: Invalid brand ID")
    try:
        response = requests.get(
            f"{BASE_URL}/get_full_brand/invalid-brand-id"
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 404:
            print("✅ Correctly returned 404 for invalid brand ID")
        else:
            print("❌ Expected 404 status code")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure the server is running")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_health_check():
    """Test if the server is running"""
    print("Testing server health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print("❌ Server health check failed")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running")
        return False

if __name__ == "__main__":
    print("Full Brand Endpoint Test")
    print("=" * 50)
    
    # First check if server is running
    if test_health_check():
        test_get_full_brand()
    else:
        print("\nPlease start the server first:")
        print("python main.py") 