from __future__ import print_function
import datetime
import os.path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dateutil import parser

# Define the scope and credentials file
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Path to your JSON key file

# Authenticate and build the service
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=creds)

# Define your local timezone
TIMEZONE = 'Asia/Kolkata'

# Replace with your actual calendar email address from the screenshot
# e.g. 'padgelwartrisha91@gmail.com'
YOUR_CALENDAR_ID = 'padgelwartrisha91@gmail.com'  # Update this!

def list_calendars():
    """Lists available calendars."""
    try:
        calendars = service.calendarList().list().execute()
        print("\n📅 Available Calendars:")
        for cal in calendars.get('items', []):
            print(f"{cal['id']} - {cal['summary']}")
        
        if not calendars.get('items'):
            print("No calendars found. This is normal for service accounts until calendars are shared with it.")
    except Exception as e:
        print(f"❌ Error fetching calendars: {e}")

def list_events(calendar_id=None):
    """Lists the upcoming 10 events."""
    if calendar_id is None:
        calendar_id = YOUR_CALENDAR_ID
        
    try:
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        print(f"Fetching events from calendar: {calendar_id}")
        events_result = service.events().list(calendarId=calendar_id, timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])
        
        if not events:
            print('No upcoming events found.')
            return []
        
        print("\n📌 Upcoming Events:")
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"{event['id']} - {start} - {event['summary']}")
        
        return events
    except Exception as e:
        print(f"❌ Error fetching events: {e}")
        print("Try running option 5 first to see available calendars")
        return []

def parse_datetime(input_str):
    """Parses a datetime string with flexible input handling."""
    try:
        return parser.parse(input_str).isoformat()
    except ValueError:
        print("❌ Invalid datetime format. Use YYYY-MM-DDTHH:MM:SS.")
        return None

def create_event():
    """Creates an event on Google Calendar."""
    summary = input("Enter event title: ")
    start_time = parse_datetime(input("Enter start time (YYYY-MM-DDTHH:MM:SS): "))
    end_time = parse_datetime(input("Enter end time (YYYY-MM-DDTHH:MM:SS): "))

    if not start_time or not end_time:
        print("❌ Event creation failed due to invalid date format.")
        return

    event = {
        'summary': summary,
        'start': {'dateTime': start_time, 'timeZone': TIMEZONE},
        'end': {'dateTime': end_time, 'timeZone': TIMEZONE},
    }
    
    try:
        created_event = service.events().insert(calendarId=YOUR_CALENDAR_ID, body=event).execute()
        print(f"✅ Event created: {created_event.get('htmlLink')}")
    except Exception as e:
        print(f"❌ Error creating event: {e}")

def delete_event():
    """Deletes an event by ID."""
    events = list_events()
    if not events:
        return

    event_id = input("Enter Event ID to delete: ")
    
    try:
        service.events().delete(calendarId=YOUR_CALENDAR_ID, eventId=event_id).execute()
        print(f"✅ Event {event_id} deleted successfully.")
    except Exception as e:
        print(f"❌ Error deleting event: {e}")

def update_event():
    """Updates an existing event."""
    events = list_events()
    if not events:
        return

    event_id = input("Enter Event ID to update: ")
    
    try:
        event = service.events().get(calendarId=YOUR_CALENDAR_ID, eventId=event_id).execute()
        
        summary = input(f"Enter new title (or press enter to keep '{event.get('summary')}'): ") or event.get('summary')
        start_time = parse_datetime(input("Enter new start time (or press enter to keep old): ")) or event['start']['dateTime']
        end_time = parse_datetime(input("Enter new end time (or press enter to keep old): ")) or event['end']['dateTime']

        event.update({'summary': summary, 'start': {'dateTime': start_time, 'timeZone': TIMEZONE}, 'end': {'dateTime': end_time, 'timeZone': TIMEZONE}})

        updated_event = service.events().update(calendarId=YOUR_CALENDAR_ID, eventId=event_id, body=event).execute()
        print(f"✅ Event updated: {updated_event.get('htmlLink')}")
    except Exception as e:
        print(f"❌ Error updating event: {e}")

def change_calendar_id():
    """Changes the calendar ID being used."""
    global YOUR_CALENDAR_ID
    YOUR_CALENDAR_ID = input("Enter calendar ID (usually your email): ")
    print(f"Calendar ID changed to: {YOUR_CALENDAR_ID}")

def main():
    """Main menu for user interaction."""
    print("\n🔑 Using service account with calendar: " + YOUR_CALENDAR_ID)
    print("⚠️ Make sure you've shared your calendar with the service account email!")
    
    while True:
        print("\n📅 Google Calendar Manager")
        print("1️⃣ List Events")
        print("2️⃣ Create Event")
        print("3️⃣ Update Event")
        print("4️⃣ Delete Event")
        print("5️⃣ List Calendars")
        print("6️⃣ Change Calendar ID")
        print("7️⃣ Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            list_events()
        elif choice == '2':
            create_event()
        elif choice == '3':
            update_event()
        elif choice == '4':
            delete_event()
        elif choice == '5':
            list_calendars()
        elif choice == '6':
            change_calendar_id()
        elif choice == '7':
            print("👋 Exiting...")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == '__main__':
    main()