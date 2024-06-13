import datetime as dt
import os.path
import random
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import timedelta
from datetime import datetime


# INITIALIZATION RITUAL

SCOPES = ["https://www.googleapis.com/auth/calendar"]

creds = None

if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json")

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port = 0)

    with open("token.json", "w") as token:
        token.write(creds.to_json())

try:
    service = build("calendar", "v3", credentials=creds)

except HttpError as error:
    print(f"An error occurred: {error}")




# this function will randomly populate my gcal with events to simulate a busy schedule, since my schedule isn't busy lol
def rand_events(service):
    calendar_id = 'primary'  # or 'your_calendar_id'

    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)

    for _ in range(50):  # number of events to generate
        # Generate a random start time
        start_time = start_date + timedelta(hours=random.randint(7, 22 * 7 - 1))

        # Generate a random end time (1-3 hours after the start time)
        end_time = start_time + timedelta(hours=random.randint(1, 3))

        # Generate a random event title
        event_title = f'Random Event {random.randint(1, 100)}'

        # Create the event
        event = {
            'summary': event_title,
            'start': {'dateTime': start_time.isoformat(timespec='seconds'), 'timeZone': 'America/New_York'},
            'end': {'dateTime': end_time.isoformat(timespec='seconds'), 'timeZone': 'America/New_York'},
        }

        # Insert the event into the calendar
        event = service.events().insert(calendarId=calendar_id, body=event).execute()

        print(f'Event created: {event.get("htmlLink")}')


# this function returns a list of all the events on a certain day in military time
def get_events_on_day(year, month, day, timezone_str):
    # Set the start and end times for the day including the full day from 00:00 to 23:59
    timezone = pytz.timezone(timezone_str)
    start_datetime = timezone.localize(datetime(year, month, day, 0, 0, 0))  # 00:00
    end_datetime = timezone.localize(datetime(year, month, day, 23, 59, 59))  # 23:59

    # Format the start and end times for the Google Calendar API
    start_datetime_iso = start_datetime.isoformat()
    end_datetime_iso = end_datetime.isoformat()

    # Get the events within the specified time range
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_datetime_iso,
        timeMax=end_datetime_iso,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    # Create a map of events
    events_map = {}
    events = events_result.get('items', [])
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        start_time = datetime.fromisoformat(start)
        end_time = datetime.fromisoformat(end)

        # Convert the start and end times to the user's timezone
        start_time = start_time.astimezone(timezone)
        end_time = end_time.astimezone(timezone)

        # Adjust start_time if it spills over from the previous day to 00:00
        if start_time < start_datetime:
            adjusted_start_time = start_datetime
        else:
            adjusted_start_time = start_time

        # Adjust end_time if it spills over to the next day to 23:59
        if end_time > end_datetime:
            adjusted_end_time = end_datetime
        else:
            adjusted_end_time = end_time

        # Format the start and end times as 4-digit numbers
        start_time_formatted = adjusted_start_time.strftime('%H%M')
        end_time_formatted = adjusted_end_time.strftime('%H%M')

        # Add the event to the map
        events_map[event['summary']] = (start_time_formatted, end_time_formatted)

    return events_map


def add_events_to_calendar(events):
    calendar_id = 'primary'

    # Add each event to the calendar
    for event in events:
        start_time = event[0]
        end_time = event[1]
        summary = event[2]
        event_body = {
            'summary': summary,
            'location': '',
            'description': '',
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
            'attendees': [],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        service.events().insert(calendarId=calendar_id, body=event_body).execute()
