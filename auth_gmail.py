from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os

# Define the required Gmail API scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def authenticate():
    creds = None

    # Load existing credentials if available
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If no valid credentials, prompt user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials2.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials in token.json
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    print("✅ Authentication successful! Token saved as 'token.json'.")

if __name__ == "__main__":
    authenticate()
