#!/usr/bin/env python3
"""
Test script for Cloudinary integration
"""

import os
from dotenv import load_dotenv
import cloudinary_utils
import imagen

# Load environment variables
load_dotenv()

def test_cloudinary_config():
    """Test if Cloudinary is properly configured"""
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
    api_key = os.getenv('CLOUDINARY_API_KEY')
    api_secret = os.getenv('CLOUDINARY_API_SECRET')
    
    print("Cloudinary Configuration Test:")
    print(f"Cloud Name: {'✓ Set' if cloud_name else '✗ Missing'}")
    print(f"API Key: {'✓ Set' if api_key else '✗ Missing'}")
    print(f"API Secret: {'✓ Set' if api_secret else '✗ Missing'}")
    
    if not all([cloud_name, api_key, api_secret]):
        print("\n❌ Cloudinary credentials are missing!")
        print("Please add the following to your .env file:")
        print("CLOUDINARY_CLOUD_NAME=your_cloud_name")
        print("CLOUDINARY_API_KEY=your_api_key")
        print("CLOUDINARY_API_SECRET=your_api_secret")
        return False
    
    print("\n✅ Cloudinary credentials are properly configured!")
    return True

def test_image_generation():
    """Test image generation and Cloudinary upload"""
    print("\nTesting image generation and Cloudinary upload...")
    
    try:
        # Test with a simple prompt
        test_prompt = "A simple blue circle on white background"
        public_id = "toothai/test/simple_test"
        
        print(f"Generating image with prompt: '{test_prompt}'")
        cloudinary_url = imagen.generate_image(test_prompt, public_id=public_id)
        
        if cloudinary_url:
            print(f"✅ Success! Image uploaded to: {cloudinary_url}")
            return True
        else:
            print("❌ Failed to generate and upload image")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    print("=== Cloudinary Integration Test ===\n")
    
    # Test configuration
    config_ok = test_cloudinary_config()
    
    if config_ok:
        # Test image generation
        test_image_generation()
    else:
        print("\nPlease configure Cloudinary credentials before running image tests.") 