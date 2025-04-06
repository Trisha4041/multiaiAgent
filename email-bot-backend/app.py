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
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
import time
import re
import dateparser
from dateparser.search import search_dates
# Configure logging
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

# CORS
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

class ExtractDateRequest(BaseModel):
    snippet: str

# Services
gmail_service = None
calendar_service = None

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
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise RuntimeError(f"Service initialization failed: {e}")

# Improved date extractor

def extract_dates(text: str) -> List[str]:
    combined_text = ' '.join(text.splitlines())

    # Match date like: April 10th, 2025
    date_pattern = r'((?:\d{1,2}(?:st|nd|rd|th)?\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s*\d{4})?)'

    # Match time like: 3:00 PM or 3 PM
    time_pattern = r'(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))'

    date_match = re.search(date_pattern, combined_text, re.IGNORECASE)
    time_match = re.search(time_pattern, combined_text, re.IGNORECASE)

    if date_match:
        date_str = date_match.group()
        parsed_date = dateparser.parse(date_str, settings={'PREFER_DATES_FROM': 'future'})
        if not parsed_date:
            return []

        if time_match:
            time_str = time_match.group()
            parsed_time = dateparser.parse(time_str)
            if parsed_time:
                combined = parsed_date.replace(hour=parsed_time.hour, minute=parsed_time.minute)
                return [combined.isoformat()]
        
        # Only date
        return [parsed_date.isoformat()]
    
    return []


@app.post("/extract-dates")
def extract_dates_from_email(request: ExtractDateRequest):
    if not request.snippet:
        raise HTTPException(status_code=400, detail="Missing email snippet.")
    extracted_dates = extract_dates(request.snippet)
    return {"dates": extracted_dates}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=4, max=10), retry=retry_if_exception_type((HttpError, TimeoutError)))
def fetch_unread_messages(service) -> dict:
    return service.users().messages().list(userId="me", q="is:unread", maxResults=5, fields="messages(id),nextPageToken").execute()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=5), retry=retry_if_exception_type((HttpError, TimeoutError)))
def get_message_details(service, message_id: str) -> dict:
    return service.users().messages().get(userId="me", id=message_id, format="metadata", metadataHeaders=["From", "Subject", "Date"]).execute()

@app.get("/unread-emails", response_model=dict)
async def get_unread_emails():
    try:
        gmail, _ = get_services()
        response = fetch_unread_messages(gmail)
        messages = response.get("messages", [])
        if not messages:
            return {"emails": []}
        unread_emails = []
        for msg in messages:
            try:
                email_data = get_message_details(gmail, msg["id"])
                headers = {header["name"].lower(): header["value"] for header in email_data.get("payload", {}).get("headers", [])}
                snippet = email_data.get("snippet", "")
                email_info = {
                    "id": msg["id"],
                    "from": headers.get("from", "Unknown Sender"),
                    "subject": headers.get("subject", "No Subject"),
                    "date": headers.get("date", "Unknown Date"),
                    "snippet": snippet,
                    "potentialDates": extract_dates(snippet)
                }
                unread_emails.append(email_info)
            except Exception as e:
                logger.warning(f"Skipping message {msg['id']} due to error: {str(e)}")
        return {"emails": unread_emails}
    except Exception as e:
        logger.error(f"Error fetching unread emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mark-as-read")
async def mark_email_as_read(request: MarkAsReadRequest):
    try:
        gmail, _ = get_services()
        gmail.users().messages().modify(userId="me", id=request.message_id, body={"removeLabelIds": ["UNREAD"]}).execute()
        return {"status": "Email marked as read"}
    except Exception as e:
        logger.error(f"Error marking email as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-email")
async def send_email(request: EmailRequest):
    try:
        gmail, _ = get_services()
        message = MIMEText(request.body)
        message["to"] = request.to
        message["subject"] = request.subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        gmail.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        return {"status": "Email sent successfully"}
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-event")
async def create_event(request: CreateEventRequest):
    try:
        _, calendar = get_services()
        
        # Log the incoming date/time values
        logger.info(f"Received start_datetime: {request.start_datetime}")
        logger.info(f"Received end_datetime: {request.end_datetime}")
        
        # Force explicit times - hardcoded approach
        # Extract just the date part from the incoming datetime
        date_part = request.start_datetime.split('T')[0]
        
        # Create explicit ISO8601 formatted times at 15:00 and 16:00
        start_iso = f"{date_part}T15:00:00"

        end_iso = f"{date_part}T16:00:00+05:30"
        
        logger.info(f"Using fixed start time: {start_iso}")
        logger.info(f"Using fixed end time: {end_iso}")
        
        event = {
            "summary": request.summary,
            "description": request.description,
            "start": {"dateTime": start_iso, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_iso, "timeZone": "Asia/Kolkata"},
            "attendees": [{"email": email} for email in request.attendees or []]
        }
        
        # Log the event being sent to Google Calendar API
        logger.info(f"Creating event with data: {json.dumps(event)}")
        
        created_event = calendar.events().insert(calendarId="primary", body=event).execute()
        
        # Log the created event response
        logger.info(f"Created event response: {json.dumps(created_event)}")
        
        return {"status": "Event created", "eventId": created_event["id"]}
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    try:
        gmail, calendar = get_services()
        gmail.users().getProfile(userId="me").execute()
        calendar.calendarList().list().execute()
        return {"status": "healthy", "message": "Services are running normally"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
