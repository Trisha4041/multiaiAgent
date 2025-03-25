from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import os.path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dateutil import parser

app = Flask(__name__)
CORS(app)

# Define the scope and credentials file
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Path to your JSON key file

# Define your local timezone
TIMEZONE = 'Asia/Kolkata'

# Global variable for calendar ID
YOUR_CALENDAR_ID = 'padgelwartrisha91@gmail.com'  # Update this!

def get_calendar_service():
    """Authenticate and build the Google Calendar service."""
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return build('calendar', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error creating service: {e}")
        return None

@app.route('/calendars', methods=['GET'])
def list_calendars():
    """Lists available calendars."""
    service = get_calendar_service()
    if not service:
        return jsonify({"error": "Could not create calendar service"}), 500
    
    try:
        calendars = service.calendarList().list().execute()
        return jsonify(calendars.get('items', []))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/events', methods=['GET'])
def list_events():
    """Lists upcoming events."""
    service = get_calendar_service()
    if not service:
        return jsonify({"error": "Could not create calendar service"}), 500
    
    try:
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId=YOUR_CALENDAR_ID, 
            timeMin=now,
            maxResults=10, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return jsonify(events_result.get('items', []))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/events', methods=['POST'])
def create_event():
    """Creates a new event."""
    service = get_calendar_service()
    if not service:
        return jsonify({"error": "Could not create calendar service"}), 500
    
    data = request.json
    try:
        event = {
            'summary': data.get('summary'),
            'start': {
                'dateTime': data.get('startTime'),
                'timeZone': TIMEZONE
            },
            'end': {
                'dateTime': data.get('endTime'),
                'timeZone': TIMEZONE
            },
        }
        
        created_event = service.events().insert(calendarId=YOUR_CALENDAR_ID, body=event).execute()
        return jsonify(created_event), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    """Updates an existing event."""
    service = get_calendar_service()
    if not service:
        return jsonify({"error": "Could not create calendar service"}), 500
    
    data = request.json
    try:
        event = service.events().get(calendarId=YOUR_CALENDAR_ID, eventId=event_id).execute()
        
        # Update event details
        event['summary'] = data.get('summary', event.get('summary'))
        event['start']['dateTime'] = data.get('startTime', event['start']['dateTime'])
        event['end']['dateTime'] = data.get('endTime', event['end']['dateTime'])

        updated_event = service.events().update(
            calendarId=YOUR_CALENDAR_ID, 
            eventId=event_id, 
            body=event
        ).execute()
        return jsonify(updated_event)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Deletes an event."""
    service = get_calendar_service()
    if not service:
        return jsonify({"error": "Could not create calendar service"}), 500
    
    try:
        service.events().delete(calendarId=YOUR_CALENDAR_ID, eventId=event_id).execute()
        return '', 204
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/calendar-id', methods=['PUT'])
def change_calendar_id():
    """Changes the global calendar ID."""
    global YOUR_CALENDAR_ID
    data = request.json
    YOUR_CALENDAR_ID = data.get('calendarId', YOUR_CALENDAR_ID)
    return jsonify({"calendarId": YOUR_CALENDAR_ID})

if __name__ == '__main__':
    app.run(debug=True, port=5000)