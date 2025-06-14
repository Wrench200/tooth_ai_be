import os



# Set your API token (make sure this is securely stored in production)
api_token = os.getenv("REPLICATE_API_TOKEN")  # Assumes it's already set in the environment
# api_token = os.environ['replicate_api_token']
# server_address = os.environ['server_address']
server_address = os.getenv('SERVER_ADDRESS')