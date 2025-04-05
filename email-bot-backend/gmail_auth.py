import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# Define the required scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar'
]

def authenticate():
    """Authenticate with Google APIs and save credentials."""
    # Delete old token if exists to force fresh authentication
    if os.path.exists('token.json'):
        os.remove('token.json')
        print("Removed old token.json")

    try:
        # Set up the OAuth 2.0 flow
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials2.json', 
            SCOPES
        )

        # Run the local server to get credentials
        credentials = flow.run_local_server(
            port=0,
            authorization_prompt_message='Please visit this URL: {url}',
            success_message='The auth flow is complete; you may close this window.',
            open_browser=True
        )

        # Save the credentials
        with open('token.json', 'w') as token:
            json.dump({
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }, token)

        print("Authentication successful! Credentials saved to token.json")
        print(f"Granted scopes: {credentials.scopes}")

    except Exception as e:
        print(f"Authentication failed: {str(e)}")
        return None

if __name__ == '__main__':
    authenticate()