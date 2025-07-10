#!/usr/bin/env python3
"""
Keep-alive script for ToothAI app on Render
Pings the health endpoint every 10 minutes to prevent sleep
"""

import requests
import time
import os
from datetime import datetime

# Get the app URL from environment variable or use default
APP_URL = os.getenv('APP_URL', 'https://your-app-name.onrender.com')

def ping_app():
    """Ping the health endpoint to keep the app awake"""
    try:
        response = requests.get(f"{APP_URL}/health", timeout=30)
        if response.status_code == 200:
            print(f"[{datetime.now()}] ✅ App is awake - Status: {response.json()}")
            return True
        else:
            print(f"[{datetime.now()}] ⚠️ App responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] ❌ Failed to ping app: {e}")
        return False

def main():
    """Main function to keep the app alive"""
    print(f"Starting keep-alive script for {APP_URL}")
    print("Pinging every 10 minutes...")
    
    while True:
        ping_app()
        # Wait 10 minutes before next ping
        time.sleep(600)  # 600 seconds = 10 minutes

if __name__ == "__main__":
    main() 