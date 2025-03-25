import os
import base64
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure API Key is set
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not TOGETHER_API_KEY:
    print("❌ ERROR: Together AI API key is missing. Set it using export TOGETHER_API_KEY='your_key_here'")
    exit(1)

# Authenticate Gmail API
try:
    creds = Credentials.from_authorized_user_file("token.json", scopes=["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.readonly"])
    gmail_service = build("gmail", "v1", credentials=creds)
except Exception as e:
    print(f"❌ ERROR: Failed to authenticate Gmail API. {e}")
    exit(1)

# Function to fetch previous emails
def fetch_emails(subject):
    try:
        # Fetch up to 15 emails based on the subject
        response = gmail_service.users().messages().list(userId="me", q=f"subject:{subject}", maxResults=15).execute()
        messages = response.get("messages", [])

        if not messages:
            return "No previous email history found."

        email_threads = []
        for msg in messages:
            email_data = gmail_service.users().messages().get(userId="me", id=msg["id"]).execute()
            snippet = email_data.get("snippet", "")
            email_threads.append(snippet)

        return "\n".join(email_threads)

    except Exception as e:
        print(f"⚠️ WARNING: Failed to fetch email history. {e}")
        return "No previous email history available."

# Function to generate AI-generated email
def generate_email(subject, email_history):
    api_url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.1",  # Correct model name
        "messages": [
            {"role": "system", "content": "You are an AI email assistant."},
            {"role": "user", "content": f"Based on this email history:\n{email_history}\nGenerate a professional email response for the subject: '{subject}'"}
        ],
        "max_tokens": 200
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"].strip()
        else:
            print("❌ ERROR: Together AI returned an unexpected response format.")
            return None

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP ERROR: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"❌ REQUEST ERROR: {req_err}")
    except KeyError:
        print("❌ ERROR: Unexpected response from Together AI.")
    
    return None

# Function to send email
def send_email(to, subject, body):
    try:
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        
        gmail_service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        print("✅ Email sent successfully!")

    except Exception as e:
        print(f"❌ ERROR: Failed to send email. {e}")

# Function to show previous emails
def show_previous_emails():
    subject = input("📌 Enter subject to fetch previous emails: ").strip()
    print("\n🔍 Fetching email history...")
    email_history = fetch_emails(subject)
    print("\n📧 Previous Emails:\n", email_history)

# Main bot function
def email_bot():
    while True:
        print("\nChoose an option:")
        print("1. Create and send a new email")
        print("2. Show previous emails")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1/2/3): ").strip()

        if choice == "1":
            to = input("📩 Enter recipient's email: ").strip()
            subject = input("📌 Enter subject of the email: ").strip()

            print("\n🔍 Fetching email history...")
            email_history = fetch_emails(subject)

            print("\n📝 Generating AI-powered email...")
            email_body = generate_email(subject, email_history)

            if not email_body:
                print("❌ AI could not generate an email. Try again.")
                continue

            print("\n💬 Generated Email:\n", email_body)
            confirm = input("\n📤 Do you want to send this email? (yes/no): ").strip().lower()
            
            if confirm == "yes":
                send_email(to, subject, email_body)
            else:
                print("❌ Email not sent.")

        elif choice == "2":
            show_previous_emails()

        elif choice == "3":
            print("👋 Exiting the program.")
            break

        else:
            print("❌ Invalid choice. Please select again.")

# Run script
if __name__ == "__main__":
    email_bot()
