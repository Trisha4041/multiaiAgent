import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

# Get the API key
api_key = os.getenv("TOGETHER_API_KEY")

# Check if the API key is loaded correctly
if not api_key:
    raise ValueError("API key not found! Make sure .env file is set up correctly.")

# Define API endpoint
url = "https://api.together.xyz/v1/chat/completions"

# Define request payload
payload = {
    "model": "mistralai/Mistral-7B-Instruct-v0.1",
    "messages": [{"role": "user", "content": "Hello!"}]
}

# Define request headers
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Send request
response = requests.post(url, json=payload, headers=headers)

# Print response
print(response.json())
