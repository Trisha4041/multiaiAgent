import os
import base64
import json
import logging
import re
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
import time

# Configure logging and silence discovery_cache warnings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# Initialize FastAPI app
app = FastAPI(
    title="Email Assistant API",
    version="1.0.0",
    description="API for managing emails and calendar events"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str

class GenerateEmailRequest(BaseModel):
    subject: str
    email_history: Optional[List[str]] = None

class MarkAsReadRequest(BaseModel):
    message_id: str

class CreateEventRequest(BaseModel):
    summary: str
    description: Optional[str] = None
    start_datetime: str
    end_datetime: str
    attendees: Optional[List[str]] = None

# Global variables for services
gmail_service = None
calendar_service = None

# Initialize Gmail and Calendar services
def get_services() -> Tuple:
    global gmail_service, calendar_service
    if gmail_service and calendar_service:
        return gmail_service, calendar_service
    try:
        token_path = "token.json"
        if not os.path.exists(token_path):
            logger.error(f"Token file not found at {token_path}")
            raise FileNotFoundError(f"Authentication token file not found: {token_path}")
        creds = Credentials.from_authorized_user_file(
            token_path,
            scopes=[
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.modify",
                "https://www.googleapis.com/auth/calendar"
            ]
        )
        gmail_service = build("gmail", "v1", credentials=creds, static_discovery=False)
        calendar_service = build("calendar", "v3", credentials=creds, static_discovery=False)
        logger.info("Gmail and Calendar API services initialized successfully")
        return gmail_service, calendar_service
    except FileNotFoundError as e:
        logger.error(f"Authentication error: {e}")
        raise RuntimeError(f"Authentication failed: {e}")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise RuntimeError(f"Service initialization failed: {e}")

# Helper functions
def extract_dates(text: str) -> List[str]:
    date_patterns = [
        r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?)\b',
        r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?)\b',
        r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b',
        r'\b(\d{4}-\d{2}-\d{2})\b'
    ]
    found_dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found_dates.extend(matches)
    return found_dates

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), retry=retry_if_exception_type((HttpError, TimeoutError)))
def fetch_unread_messages(service) -> dict:
    return service.users().messages().list(
        userId="me",
        q="is:unread",
        maxResults=20,
        fields="messages(id),nextPageToken"
    ).execute()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=5), retry=retry_if_exception_type((HttpError, TimeoutError)))
def get_message_details(service, message_id: str) -> dict:
    return service.users().messages().get(
        userId="me",
        id=message_id,
        format="metadata",
        metadataHeaders=["From", "Subject", "Date"]
    ).execute()

@app.get("/unread-emails", response_model=dict)
async def get_unread_emails():
    try:
        gmail, _ = get_services()
        logger.info("Fetching unread emails")
        start_time = time.time()
        response = fetch_unread_messages(gmail)
        messages = response.get("messages", [])
        if not messages:
            logger.info("No unread emails found")
            return {"emails": []}
        unread_emails = []
        for msg in messages:
            try:
                email_data = get_message_details(gmail, msg["id"])
                headers = {header["name"].lower(): header["value"] for header in email_data.get("payload", {}).get("headers", [])}
                email_info = {
                    "id": msg["id"],
                    "from": headers.get("from", "Unknown Sender"),
                    "subject": headers.get("subject", "No Subject"),
                    "date": headers.get("date", "Unknown Date"),
                    "snippet": email_data.get("snippet", ""),
                    "potentialDates": extract_dates(email_data.get("snippet", ""))
                }
                unread_emails.append(email_info)
            except Exception as e:
                logger.warning(f"Skipping message {msg['id']} due to error: {str(e)}")
                continue
        logger.info(f"Fetched {len(unread_emails)} unread emails in {time.time() - start_time:.2f}s")
        return {"emails": unread_emails}
    except HttpError as e:
        logger.error(f"Gmail API error: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Gmail API service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching emails: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch unread emails: {str(e)}")

@app.post("/mark-as-read", status_code=status.HTTP_200_OK)
async def mark_email_as_read(request: MarkAsReadRequest):
    try:
        gmail, _ = get_services()
        logger.info(f"Marking email {request.message_id} as read")
        gmail.users().messages().modify(userId="me", id=request.message_id, body={"removeLabelIds": ["UNREAD"]}).execute()
        return {"status": "Email marked as read"}
    except HttpError as e:
        logger.error(f"Failed to mark email as read: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid message ID: {str(e)}")
    except Exception as e:
        logger.error(f"Error marking email as read: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to mark email as read: {str(e)}")

@app.post("/send-email", status_code=status.HTTP_200_OK)
async def send_email(request: EmailRequest):
    try:
        gmail, _ = get_services()
        message = MIMEText(request.body)
        message["to"] = request.to
        message["subject"] = request.subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        gmail.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        return {"status": "Email sent successfully"}
    except HttpError as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid email parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send email: {str(e)}")

@app.get("/fetch-emails", response_model=dict)
async def fetch_emails_by_subject(subject: str):
    try:
        gmail, _ = get_services()
        query = f"subject:{subject}"
        response = gmail.users().messages().list(userId="me", q=query, maxResults=10).execute()
        messages = response.get("messages", [])
        if not messages:
            return {"emails": []}
        email_history = []
        for msg in messages:
            try:
                email_data = gmail.users().messages().get(userId="me", id=msg["id"], format="full").execute()
                headers = {header["name"].lower(): header["value"] for header in email_data.get("payload", {}).get("headers", [])}
                parts = email_data.get("payload", {}).get("parts", [])
                body = ""
                if parts:
                    for part in parts:
                        if part.get("mimeType") == "text/plain":
                            body_data = part.get("body", {}).get("data", "")
                            if body_data:
                                body += base64.urlsafe_b64decode(body_data).decode("utf-8")
                else:
                    body_data = email_data.get("payload", {}).get("body", {}).get("data", "")
                    if body_data:
                        body = base64.urlsafe_b64decode(body_data).decode("utf-8")
                email_entry = f"From: {headers.get('from', 'Unknown')}\nTo: {headers.get('to', 'Unknown')}\nDate: {headers.get('date', 'Unknown')}\nSubject: {headers.get('subject', 'No Subject')}\n\n{body}"
                email_history.append(email_entry)
            except Exception as e:
                logger.warning(f"Error processing message {msg['id']}: {str(e)}")
                continue
        return {"emails": email_history}
    except HttpError as e:
        logger.error(f"Gmail API error: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Gmail API service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching emails: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch emails: {str(e)}")

@app.post("/generate-email", status_code=status.HTTP_200_OK)
async def generate_email(request: GenerateEmailRequest):
    try:
        subject = request.subject
        history = request.email_history or []

        prompt = f"You are an email assistant. Write a professional email reply based on the following subject and history.\n\n"
        prompt += f"Subject: {subject}\n\n"
        if history:
            for i, email in enumerate(history[:3]):
                prompt += f"Email {i+1}:\n{email[:500]}\n\n"
        prompt += "Compose the reply email below:\n\n"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {TOGETHER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                    "messages": [
                        {"role": "system", "content": "You are a helpful email assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 512
                }
            )
            response.raise_for_status()
            data = response.json()
            generated_content = data['choices'][0]['message']['content']
            return {"email_content": generated_content}
    except httpx.HTTPStatusError as e:
        logger.error(f"Together API returned error: {e.response.text}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to get response from AI model.")
    except Exception as e:
        logger.error(f"Error generating email: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate email content: {str(e)}")

@app.post("/create-event", status_code=status.HTTP_201_CREATED)
async def create_calendar_event(request: CreateEventRequest):
    try:
        _, calendar = get_services()
        attendees = [{'email': email} for email in request.attendees if email] if request.attendees else []
        event = {
            'summary': request.summary,
            'description': request.description or "",
            'start': {'dateTime': request.start_datetime, 'timeZone': 'UTC'},
            'end': {'dateTime': request.end_datetime, 'timeZone': 'UTC'},
            'attendees': attendees
        }
        created_event = calendar.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
        return {
            "status": "Event created",
            "eventId": created_event.get('id'),
            "htmlLink": created_event.get('htmlLink')
        }
    except HttpError as e:
        logger.error(f"Failed to create event: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid event parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create event: {str(e)}")

@app.get("/health")
async def health_check():
    try:
        gmail, calendar = get_services()
        gmail.users().getProfile(userId="me").execute()
        calendar.calendarList().list().execute()
        return {"status": "healthy", "message": "Services are running normally"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Service unavailable: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
