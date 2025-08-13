# Set your API token (make sure this is securely stored in production) ok
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
api_token = os.getenv("REPLICATE_API_TOKEN")  # Assumes it's already set in the environment
openai_api_key = os.getenv("OPENAI_API_KEY") 
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not api_token:
    print("WARNING: REPLICATE_API_TOKEN not found in environment variables!")
    print("Make sure you have a .env file with: REPLICATE_API_TOKEN=your_token_here")
else:
    print(f"API token loaded successfully: {api_token[:10]}...")

# api_token = "r8_AVRihwc69CfEIKMWdhBQesMJmIXzfU80eaII2"
server_address = "http://127.0.0.1:8080"