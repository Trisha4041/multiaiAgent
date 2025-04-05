from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # ✅ Import this
from pydantic import BaseModel
import datetime
from dateutil import parser
from google.oauth2 import service_account
from googleapiclient.discovery import build

# FastAPI instance
app = FastAPI()

# ✅ Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'credentials.json'
TIMEZONE = 'Asia/Kolkata'
YOUR_CALENDAR_ID = 'padgelwartrisha91@gmail.com'  # Replace with your calendar email

# Google Calendar API service
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=creds)

# Request schemas
class EventCreate(BaseModel):
    summary: str
    start: str  # ISO format
    end: str    # ISO format

class EventUpdate(BaseModel):
    event_id: str
    summary: str = None
    start: str = None
    end: str = None

@app.get("/events")
def list_events():
    try:
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId=YOUR_CALENDAR_ID, timeMin=now,
            maxResults=10, singleEvents=True, orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching events: {str(e)}")

@app.post("/events")
def create_event(event: EventCreate):
    try:
        parsed_start = parser.parse(event.start).isoformat()
        parsed_end = parser.parse(event.end).isoformat()

        event_body = {
            'summary': event.summary,
            'start': {'dateTime': parsed_start, 'timeZone': TIMEZONE},
            'end': {'dateTime': parsed_end, 'timeZone': TIMEZONE}
        }

        created_event = service.events().insert(
            calendarId=YOUR_CALENDAR_ID, body=event_body
        ).execute()

        return {"message": "Event created", "link": created_event.get("htmlLink")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")

@app.put("/events")
def update_event(event: EventUpdate):
    try:
        current = service.events().get(calendarId=YOUR_CALENDAR_ID, eventId=event.event_id).execute()

        updated_event = {
            'summary': event.summary or current['summary'],
            'start': {
                'dateTime': parser.parse(event.start).isoformat() if event.start else current['start']['dateTime'],
                'timeZone': TIMEZONE
            },
            'end': {
                'dateTime': parser.parse(event.end).isoformat() if event.end else current['end']['dateTime'],
                'timeZone': TIMEZONE
            }
        }

        current.update(updated_event)
        updated = service.events().update(calendarId=YOUR_CALENDAR_ID, eventId=event.event_id, body=current).execute()

        return {"message": "Event updated", "link": updated.get("htmlLink")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating event: {str(e)}")

@app.delete("/events/{event_id}")
def delete_event(event_id: str):
    try:
        service.events().delete(calendarId=YOUR_CALENDAR_ID, eventId=event_id).execute()
        return {"message": f"Event {event_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting event: {str(e)}")

@app.get("/calendars")
def list_calendars():
    try:
        calendars = service.calendarList().list().execute()
        return {"calendars": calendars.get('items', [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching calendars: {str(e)}")
