import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# Set up the OAuth 2.0 flow
flow = InstalledAppFlow.from_client_secrets_file(
    'credentials2.json', 
    ['https://www.googleapis.com/auth/gmail.send', 
     'https://www.googleapis.com/auth/gmail.readonly']
)

# Run the local server to get credentials
credentials = flow.run_local_server(port=0)

# Save the credentials to a JSON file
with open('token.json', 'w') as token:
    json.dump({
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }, token)

print("Credentials saved successfully!")