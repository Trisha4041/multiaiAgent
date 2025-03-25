from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import json

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

flow = InstalledAppFlow.from_client_secrets_file("credentials2.json", SCOPES)
creds = flow.run_local_server(port=0)

# Save the credentials to token.json
with open("token.json", "w") as token:
    token.write(creds.to_json())

print("✅ New token.json has been generated successfully!")

